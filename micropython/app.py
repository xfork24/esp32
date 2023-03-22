from display import init_oled
from qr import QRCode


def main():
    qr = QRCode(border=2)
    qr.add_data('http://175.178.162.201:18083/')
    matrix = qr.get_matrix()

    row_len = len(matrix)
    col_len = len(matrix[0])

    scale_rate = 1
    oled = init_oled()

    for x in range(row_len * scale_rate):
        for y in range(col_len * scale_rate):
            if matrix[x // scale_rate][y // scale_rate]:
                oled.pixel(x, y + 16, 0xffff)
            y += 1
        x += 1
    oled.show()


if __name__ == '__main__':
    main()
