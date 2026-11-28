extends Node3D

@onready var camera_3d: Camera3D = $Camera3D
var server: UDPServer = UDPServer.new()
var peers: Array[PacketPeerUDP] = []

@export var port: int = 4200

func _ready() -> void:
	server.listen(port) 
	print("UDP Server is listening on port " + str(port))

func _process(delta: float) -> void:
	server.poll()
	
	if server.is_connection_available():
		var peer: PacketPeerUDP = server.take_connection()
		peers.append(peer)
		print("Accepted connection from: %s:%s" % [peer.get_packet_ip(), peer.get_packet_port()])
	
	if peers.size() > 0:
		send_camera_feed()

func send_camera_feed():
	var image: Image = camera_3d.get_viewport().get_texture().get_image()
	var byte_array = image.save_png_to_buffer()  
	
	var chunk_size = 8192 
	for i in range(0, byte_array.size(), chunk_size):
		var chunk = byte_array.slice(i, i + chunk_size)
		for peer in peers:
			peer.put_packet(chunk)
