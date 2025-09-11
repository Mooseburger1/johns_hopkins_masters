import socket
HOST = "192.168.1.37"
PORT = 12345

my_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
my_socket.settimeout(5.0)

def main():
    while True:
        date = b"12, september, 2025, 12, 8, 20"
        my_socket.sendto(date, (HOST, PORT))
        color_or_quit = input("Enter a Color or 'quit' to end the program: \n")
        if color_or_quit == 'quit':
            break

        sendColor=color_or_quit.encode()
        my_socket.sendto(sendColor, (HOST, PORT))
        print('Sent ' + color_or_quit + ' to HOST ', HOST, PORT )

if __name__ == "__main__":
    main()