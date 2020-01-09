# keep-wifi-up

Application that workarounds issues that prevent NetworkManager from reconnecting to a
WiFi network

## How it works

At start the application checks which WiFi network is currently activated. If no network
is yet activated it awaits for one to be activated.

Then it enters a loop that checks each minute whether the detected WiFi network is
still connected.

If connectivity to the network is no longer available, the application waits another
minute, checks again and if the connection is still not established it triggers
activation.

If there is no change after one more minute the application restarts the NetworkManager
service. If restarting NetworkManager does not help, the application considers the network
unavailable and awaits to it to become available again.

If during the checks the device switches to another WiFi network the applications detects
this and operates on top of it.
