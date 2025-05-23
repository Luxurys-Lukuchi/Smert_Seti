import numpy as np
import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation
from matplotlib.table import Table


def lambda_t(t):
    return 1 - 0.01 * np.abs(t - 70)


def simulate_non_homogeneous_poisson(T, lambda_max):
    t = 0
    events = []
    while t <= T:
        u1 = np.random.uniform(0, 1)
        t += -np.log(u1) / lambda_max
        if t > T:
            break
        u2 = np.random.uniform(0, 1)
        if u2 <= lambda_t(t) / lambda_max:
            events.append(t)
    return events



T = 100
lambda_max = max(lambda_t(t) for t in np.linspace(0, T, 1000))

events = simulate_non_homogeneous_poisson(T, lambda_max)
events.sort()

fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(12, 10), gridspec_kw={'height_ratios': [3, 1]})
fig.suptitle('Моделирование 8 вариант')

ax1.set_xlim(0, T)
ax1.set_ylim(0, len(events) + 1)
ax1.set_xlabel('Время (t)')
ax1.set_ylabel('Количество событий (N)')
ax1.grid(True)
line, = ax1.plot([], [], 'b-', drawstyle='steps-post', label='Моделируемый поток')
ax1.legend()

ax2.axis('off')
table = ax2.table(cellText=[[''] * 5 for _ in range((len(events) // 5) + 1)],
                  colLabels=[f' ' for i in range(5)],
                  loc='center')
table.auto_set_font_size(False)
table.set_fontsize(10)
table.scale(1, 1.5)


def init():
    line.set_data([], [])
    return line,


def update(frame):
    current_events = events[:frame + 1]
    y = np.arange(1, frame + 2)
    line.set_data(current_events, y)

    for i in range(5):
        for j in range((len(events) // 5) + 1):
            idx = j * 5 + i
            if idx < len(events) and idx <= frame:
                table._cells[(j + 1, i)]._text.set_text(f'{events[idx]:.2f}')
            elif idx > frame:
                table._cells[(j + 1, i)]._text.set_text('')

    return line,


ani = FuncAnimation(fig, update, frames=len(events),
                    init_func=init, blit=False, interval=200, repeat=False)

plt.tight_layout()
plt.show()

print("Все моменты событий:", events)