#!/usr/bin/env python

import dbus

import gi
gi.require_version("NM", "1.0")
from gi.repository import NM, GLib

AWAIT_INITIAL_CONNECTION_INTERVAL = 5
RECHECK_INTERVAL = 60

APPNAME = "keep-wifi-up"

class State:
    def __init__(self):
        self.main_loop = GLib.MainLoop()

        self.system_bus = dbus.SystemBus()

        self.nm_client = NM.Client.new(None)

        self.await_initial_connection = False

        self.connection_id = ''
        self.connection_uuid = None

        self.disconnected_checks = 0

def get_active_wifi_connection(nm_client):
    active_connections = nm_client.get_active_connections()

    for active_connection in active_connections:
        devices = active_connection.get_devices()

        for device in devices:
            if device.get_device_type() == NM.DeviceType.WIFI:
                return active_connection

    return None

def store_connection(state, active_connection):
    state.connection_id = active_connection.get_id()
    state.connection_uuid = active_connection.get_uuid()
    log("Active connection: {} [{}]".format(state.connection_id, state.connection_uuid))

def update_connection(state, active_connection):
    uuid = active_connection.get_uuid()
    if state.connection_uuid != uuid:
        state.connection_uuid = uuid
        state.connection_id = active_connection.get_id()
        log("New connection ID: {}".format(state.connection_id))
        log("New UUID: {}".format(state.connection_uuid))
    else:
        log("Still active...")


def get_and_store_initial_wifi_connection(state):
    active_connection = get_active_wifi_connection(state.nm_client)

    if active_connection is not None:
        store_connection(state, active_connection)
        GLib.timeout_add_seconds(
            RECHECK_INTERVAL,
            check_for_active_connection,
            state
        )
        return

    if state.await_initial_connection == False:
        log("Awaiting active WiFi connection")
        state.await_initial_connection = True

    GLib.timeout_add_seconds(
        AWAIT_INITIAL_CONNECTION_INTERVAL,
        get_and_store_initial_wifi_connection,
        state
    )

def check_for_active_connection(state):
    active_connection = get_active_wifi_connection(state.nm_client)

    if active_connection is not None:
        update_connection(state, active_connection)
        state.disconnected_checks = 0
    else:
        if state.disconnected_checks == 0:
            log("Disconnected")
        state.disconnected_checks += 1
        if state.disconnected_checks == 2:
            reactivate_connection(state)
        elif state.disconnected_checks == 3:
            restart_network_manager(state)
        elif state.disconnected_checks == 4:
            log("Network could be down...")

    GLib.timeout_add_seconds(
        RECHECK_INTERVAL,
        check_for_active_connection,
        state
    )

def activate_connection_callback(client, result, _data):
    try:
        client.activate_connection_finish(result)
        log("Successfully activated")
    except Exception as e:
        log("Failed activating connection: {}".format(e))

def reactivate_connection(state):
    log("Reactivate {}".format(state.connection_id))

    connection = state.nm_client.get_connection_by_uuid(state.connection_uuid)

    state.nm_client.activate_connection_async(
        connection,
        None,
        None,
        None,
        activate_connection_callback,
        None
    )

def restart_network_manager(state):
    log("Restarting NetworkManager...")
    system_bys = dbus.SystemBus()
    systemd = system_bys.get_object("org.freedesktop.systemd1", "/org/freedesktop/systemd1")
    systemd_manager = dbus.Interface(systemd, "org.freedesktop.systemd1.Manager")
    systemd_manager.RestartUnit("NetworkManager.service", "fail")

def log(msg):
    print("[{}] {}".format(APPNAME, msg))

def main():
    state = State()

    get_and_store_initial_wifi_connection(state)

    state.main_loop.run()

main()
