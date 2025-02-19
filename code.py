import numpy as np
import pyaudio
import matplotlib.pyplot as plt
from scipy.fftpack import fft
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import tkinter as tk
import time
x1=7500
y1=8000
z1=0.5      
x2=15000
y2=15500
z2=0.5
x3=0
y3=500
z3=1  

# Настройки начального потока
initial_chunk = 4048
initial_rate = 44100
n_fft = 1024  # Размер окна для FFT

# Инициализация PyAudio
p = pyaudio.PyAudio()

# Создание главного окна приложения
root = tk.Tk()
root.title("Real-Time Audio Spectrum Analyzer")
root.configure(bg='#181818')

# Размеры окна
window_width = 1600
window_height = 1000

# Дополнительные параметры для рамок
frame_width = int(window_width * 0.85)
frame_height = int(window_height * 0.85)

# Рамка для графиков
frame_border = tk.Frame(root, bg='#303030', bd=2, relief=tk.RAISED)
frame_border.place(x=20, y=20, width=frame_width, height=frame_height)

# Функция для инициализации аудиопотока
def init_stream(chunk, rate):
    return p.open(format=pyaudio.paInt16,
                  channels=1,
                  rate=rate,
                  input=True,
                  frames_per_buffer=chunk)

# Настройка начального потока
CHUNK = initial_chunk
RATE = initial_rate
stream = init_stream(CHUNK, RATE)

# Создание графиков
fig, (ax, ax2) = plt.subplots(2, 1, facecolor='#181818', figsize=(10, 8), gridspec_kw={'height_ratios': [2, 1]})
fig.tight_layout(pad=3.0)

# Спектрограмма (первый график)
spec_data = np.zeros((n_fft // 2, 100))
spec_data.fill(1e-3)
img = ax.imshow(spec_data, aspect='auto', cmap='seismic', origin='lower',
                extent=[0, 10, 0, RATE // 2])

# Настройка внешнего вида графика
ax.set_ylim(0, RATE // 2)
ax.set_xlim(0, 10)
ax.set_facecolor('#181818')
ax.set_title("Spectrogram", color='white')
for spine in ax.spines.values():
    spine.set_color('#505050')
ax.xaxis.label.set_color('white')
ax.yaxis.label.set_color('white')
ax.tick_params(axis='x', colors='white')
ax.tick_params(axis='y', colors='white')

# Зависимость частоты от амплитуды (второй график)
line, = ax2.plot([], [], color='cyan', lw=2)
ax2.set_xlim(0, RATE // 2)
ax2.set_ylim(0, 10)
ax2.set_facecolor('#181818')
ax2.set_title("Amplitude vs Frequency", color='white')
for spine in ax2.spines.values():
    spine.set_color('#505050')
ax2.xaxis.label.set_color('white')
ax2.yaxis.label.set_color('white')
ax2.tick_params(axis='x', colors='white')
ax2.tick_params(axis='y', colors='white')
#ax2.set_ylim(0, 5)

# Привязываем график к интерфейсу Tkinter
canvas = FigureCanvasTkAgg(fig, master=frame_border)
canvas_widget = canvas.get_tk_widget()
canvas_widget.pack(fill=tk.BOTH, expand=True)

# Ползунки для CHUNK и RATE
chunk_slider = tk.Scale(root, from_=256, to=4096, orient=tk.HORIZONTAL, label='CHUNK', length=300,
                        bg='#303030', fg='white', troughcolor='#505050', font=("Arial", 10))
chunk_slider.set(CHUNK)
chunk_slider.place(x=frame_width + 40, y=20)

rate_slider = tk.Scale(root, from_=8000, to=48000, orient=tk.HORIZONTAL, label='RATE', length=300,
                       bg='#303030', fg='white', troughcolor='#505050', font=("Arial", 10))
rate_slider.set(RATE)
rate_slider.place(x=frame_width + 40, y=100)

# Создание Canvas для индикатора
indicator_canvas = tk.Canvas(root, width=100, height=50, bg='#303030', highlightthickness=0)
indicator_canvas.place(x=frame_width + 40, y=350)

# Прямоугольный индикатор (по умолчанию красный)
indicator_rect = indicator_canvas.create_rectangle(10, 10, 90, 40, fill='red')

# Временные параметры
start_time = time.time()  # Запоминаем время начала записи
recorded_time = 0  # Время, прошедшее с момента начала записи
indicator_active_time = 0  # Время, когда индикатор стал активным
indicator_active = False  # Состояние индикатора

# Целевые диапазоны частот и пороги амплитуды
target_frequency_ranges = [
    (x1, y1, z1),      
    (x2, y2, z2),
    (x3, y3, z3),  
]

# Функция для обновления параметров при изменении ползунков
def update_params(val):
    global CHUNK, RATE, stream, img, ax, recorded_time, spec_data

    CHUNK = int(chunk_slider.get())
    RATE = int(rate_slider.get())

    # Перезапуск аудиопотока с новыми параметрами
    stream.stop_stream()
    stream.close()
    stream = init_stream(CHUNK, RATE)

    # Обновление графика
    ax.set_ylim(0, RATE // 2)
    spec_data = np.zeros((n_fft // 2, 100))
    spec_data.fill(1e-3)
    img.set_data(spec_data)
    img.set_clim(vmin=np.min(spec_data), vmax=np.max(spec_data))
    img.set_extent([0, 10, 0, RATE // 2])

    update_plot(np.zeros(CHUNK))  # Очистка графика

chunk_slider.config(command=update_params)
rate_slider.config(command=update_params)



# Настройки линий
threshold_lines_config = [
    {"y": z1, "x_start": x1, "x_end": y1, "color": "red", "linestyle": "--", "label": "Threshold 1"},
    {"y": z2, "x_start": x2, "x_end": y2, "color": "green", "linestyle": "--", "label": "Threshold 2"},
]
# Рисуем линии
threshold_lines = []
for line_config in threshold_lines_config:
    line_obj, = ax2.plot(
        [line_config["x_start"], line_config["x_end"]],
        [line_config["y"], line_config["y"]],
        color=line_config["color"],
        linestyle=line_config["linestyle"],
        label=line_config["label"],
    )
    threshold_lines.append(line_obj)



# Функция для обновления графиков и индикатора
def update_plot(data):
    global RATE, CHUNK, spec_data, recorded_time, indicator_active, indicator_active_time
    
    # Вычисляем FFT
    yf = fft(data, n=n_fft)
    y_data = 2.0 / CHUNK * np.abs(yf[:n_fft // 2])  # Амплитуды
    y_data = np.log1p(y_data)

    # Сдвигаем данные спектра влево
    spec_data = np.roll(spec_data, -1, axis=1)
    spec_data[:, -1] = y_data

    # Обновление спектрограммы
    img.set_clim(vmin=np.min(spec_data), vmax=np.max(spec_data))
    img.set_data(spec_data)

    # Обновление временной оси
    recorded_time += CHUNK / RATE
    img.set_extent([0, min(10, recorded_time), 0, RATE // 2])

    # Обновление графика амплитуды
    freqs = np.linspace(0, RATE // 2, n_fft // 2)
    line.set_data(freqs, y_data)

    # Обновление индикатора
    conditions_met = all(
        np.max(y_data[(np.where((np.linspace(0, RATE // 2, n_fft // 2) >= low) & 
        (np.linspace(0, RATE // 2, n_fft // 2) <= high)))] ) > threshold
        for low, high, threshold in target_frequency_ranges
    )

    if conditions_met:
        if indicator_active:
            if time.time() - indicator_active_time >= 2:
                indicator_canvas.itemconfig(indicator_rect, fill='green')
        else:
            indicator_active_time = time.time()
            indicator_active = True
    else:
        indicator_canvas.itemconfig(indicator_rect, fill='red')
        indicator_active = False

    canvas.draw()
    canvas.flush_events()

# Основной цикл
def audio_loop():
    try:
        data = np.frombuffer(stream.read(CHUNK, exception_on_overflow=False), dtype=np.int16)
        update_plot(data)
        root.after(10, audio_loop)
    except Exception as e:
        print(f"Ошибка: {e}")

root.after(10, audio_loop)
root.geometry(f'{window_width}x{window_height}')
root.mainloop()

stream.stop_stream()
stream.close()
p.terminate()
