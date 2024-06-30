import re


def read_window_sizes(filename):
    with open(filename, 'r', encoding='utf-8') as file:
        content = file.read()
    return read_window_sizes_from_text(content)


def read_window_sizes_from_text(content):
    patterns = [
        r'(\d+)\s*[xх×*]\s*(\d+)',  # шаблон для размеров в формате 70x197
    ]
    window_sizes = []
    for pattern in patterns:
        matches = re.findall(pattern, content)
        for match in matches:
            width, height = map(int, match)
            window_sizes.append((width, height))
    return window_sizes


def calculate_all(window_sizes):
    roll_width = 152  # Ширина рулона пленки в см
    total_area = 0
    total_linear_meters = 0
    results = []
    leftovers = []

    for index, (width, height) in enumerate(window_sizes):
        area = width * height / 10000
        total_area += area

        used_leftover = None
        leftover_source = None
        for i, (leftover_width, leftover_height, source) in enumerate(leftovers):
            if leftover_width >= width and leftover_height >= height:
                used_leftover = (leftover_width, leftover_height)
                leftover_source = source
                leftovers.pop(i)
                new_leftover_width = leftover_width - width
                new_leftover_height = leftover_height - height
                if new_leftover_width > 0:
                    leftovers.append((new_leftover_width, height, source))
                if new_leftover_height > 0:
                    leftovers.append((width, new_leftover_height, source))
                break

        if used_leftover:
            result = f"Окно {index + 1}: {width}х{height} - площадь: {area:.2f} кв. м - использовать остаток {used_leftover[0]}х{used_leftover[1]} от окна {leftover_source} (новый остаток: {new_leftover_width}х{new_leftover_height})"
            results.append(result)
        else:
            linear_meters_needed = height / 100
            total_linear_meters += linear_meters_needed
            leftover_width = roll_width - width
            leftover_height = height
            if leftover_width > 0:
                leftovers.append((leftover_width, height, f'{index + 1}'))
            if leftover_height > 0:
                leftovers.append((width, leftover_height, f'{index + 1}'))
            results.append(
                f"Окно {index + 1}: {width}х{height} - площадь: {area:.2f} кв. м - отрезать {linear_meters_needed:.2f} м (остаток: {leftover_width}х{leftover_height})")

    return total_area, total_linear_meters, results, leftovers
