import os
from flask import Flask, request, render_template
from flask_cors import CORS
import re

app = Flask(__name__)
CORS(app)

UPLOAD_FOLDER = 'uploads'
ALLOWED_EXTENSIONS = {'txt'}

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

LABOR_COST = 3000
MATERIAL_COST = 2500
EXTRA_MATERIAL_COST = 2300

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def parse_window_sizes(contents):
    sizes = []
    lines = contents.split('\n')
    for line in lines:
        matches = re.findall(r'(\d+)[xх](\d+)', line)
        if matches:
            for match in matches:
                width, height = map(int, match)
                sizes.append((width, height))
    return sizes

def calculate_material_requirements(window_sizes):
    roll_width = 152
    total_area = 0
    total_length = 0
    leftovers = []
    results = []

    def use_leftover(width, height):
        nonlocal leftovers
        for i, (lw, lh) in enumerate(leftovers):
            if (lw >= width and lh >= height) or (lh >= width and lw >= height):
                new_leftover = (lw - width, lh) if lw >= width else (lw, lh - height)
                if new_leftover[0] > 0 and new_leftover[1] > 0:
                    leftovers[i] = new_leftover
                else:
                    leftovers.pop(i)
                return True, (lw, lh), new_leftover
        return False, None, None

    for index, (width, height) in enumerate(window_sizes):
        area = width * height / 10000
        total_area += area

        used, original, new_leftover = use_leftover(width, height)
        if used:
            results.append(f"Окно {index + 1}: {width}х{height} - использовать остаток {original[0]}х{original[1]} (новый остаток: {new_leftover[0]}х{new_leftover[1]})")
        else:
            if width <= roll_width and height <= roll_width:
                if width <= roll_width:
                    cut_length = (height + 5) / 100
                    new_leftover = (roll_width - width, height)
                else:
                    cut_length = (width + 5) / 100
                    new_leftover = (roll_width, height - width)
            else:
                if width > roll_width and height > roll_width:
                    cut_length = (width + 5) / 100
                    new_leftover = (roll_width, height - width)
                else:
                    cut_length = (height + 5) / 100
                    new_leftover = (roll_width - width, height)
            total_length += cut_length
            if new_leftover[0] > 0 and new_leftover[1] > 0:
                leftovers.append(new_leftover)
            results.append(f"Окно {index + 1}: {width}х{height} - отрезать {cut_length:.2f} м (остаток: {new_leftover[0]}х{new_leftover[1]})")

    extra_material_area = sum(lw * lh / 10000 for lw, lh in leftovers)
    extra_material_cost = extra_material_area * EXTRA_MATERIAL_COST
    labor_cost = total_area * LABOR_COST
    material_cost = total_area * MATERIAL_COST
    total_cost = labor_cost + material_cost + extra_material_cost

    discount = 0
    if total_area > 100:
        discount = total_cost * 0.10
        total_cost -= discount

    return {
        'total_area': total_area,
        'total_length': total_length,
        'labor_cost': labor_cost,
        'material_cost': material_cost,
        'extra_material_area': extra_material_area,
        'extra_material_cost': extra_material_cost,
        'discount': discount,
        'total_cost': total_cost,
        'results': results
    }

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        return render_template('index.html', error="Файл не найден.")
    file = request.files['file']
    if file.filename == '':
        return render_template('index.html', error="Файл не выбран.")
    if file and allowed_file(file.filename):
        filename = os.path.join(app.config['UPLOAD_FOLDER'], file.filename)
        file.save(filename)
        with open(filename, 'r', encoding='utf-8') as f:
            contents = f.read()
        window_sizes = parse_window_sizes(contents)
        if not window_sizes:
            return render_template('index.html', error="Файл не содержит корректных размеров окон.")
        calculations = calculate_material_requirements(window_sizes)
        return render_template('index.html', calculations=calculations)
    return render_template('index.html', error="Неверный формат файла.")

if __name__ == '__main__':
    app.run(debug=True)
