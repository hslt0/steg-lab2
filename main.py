"""Interactive menu for manually trying PVG image steganography."""

from pathlib import Path

from image_io import decode_image, encode_image


def main() -> None:
    while True:
        print("\nPVG — ручне тестування")
        print("1. Приховати повідомлення")
        print("2. Витягти повідомлення")
        print("0. Вийти")
        choice = input("Оберіть дію: ").strip()

        if choice == "0":
            print("Завершення.")
            return
        if choice == "1":
            input_path = Path(input("Шлях до зображення: ").strip().strip('"'))
            output_path = Path(
                input("Шлях для збереження (PNG/BMP/TIFF): ").strip().strip('"')
            )
            message = input("Повідомлення для приховування: ")
            try:
                encode_image(input_path, output_path, message)
                print(f"Повідомлення збережено у файлі: {output_path}")
            except (OSError, ValueError) as exc:
                print(f"Помилка: {exc}")
        elif choice == "2":
            input_path = Path(input("Шлях до зображення з повідомленням: ").strip().strip('"'))
            try:
                print(f"Витягнуте повідомлення: {decode_image(input_path)}")
            except (OSError, ValueError) as exc:
                print(f"Помилка: {exc}")
        else:
            print("Невідома команда. Введіть 1, 2 або 0.")


if __name__ == "__main__":
    main()
