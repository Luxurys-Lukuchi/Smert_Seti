import numpy as np
import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation


T = 100
events = []
last_service_end = 0



def lambda_t(t):
    return 1 / (abs(t - 70) + 0.01)


def mu_t(t):
    return 0.12 - 0.01 * abs(t - 50)



current_time = 0
while current_time < T:
    r = np.random.rand()
    dt = -np.log(r) / lambda_t(current_time)
    current_time += dt
    if current_time > T:
        break

    service_duration = -np.random.rand() / mu_t(current_time)

    if current_time >= last_service_end:
        events.append((current_time, 'served'))
        last_service_end = current_time + service_duration
    else:
        events.append((current_time, 'rejected'))

print(f"Общее количество событий: {len(events)}")


fig, ax = plt.subplots(figsize=(12, 3))
ax.set_xlim(0, T)
ax.set_ylim(0.9, 1.1)
ax.set_yticks([])
ax.set_xlabel("Время")
ax.set_title("Одноканальной СМО с отказами")


served_scatter, = ax.plot([], [], 'go', label='Обслуженные')
rejected_scatter, = ax.plot([], [], 'ro', label='Отказы')

served_times = []
rejected_times = []



def update(frame):
    global served_times, rejected_times

    time, status = events[frame]

    if status == 'served':
        served_times.append(time)
    else:
        rejected_times.append(time)

    served_scatter.set_data(served_times, [1] * len(served_times))
    rejected_scatter.set_data(rejected_times, [0.95] * len(rejected_times))


    if len(served_times) > 0 or len(rejected_times) > 0:
        max_x = max(max(served_times, default=0), max(rejected_times, default=0))
        ax.set_xlim(0, max(max_x + 5, 10))

    return served_scatter, rejected_scatter



ani = FuncAnimation(fig, update, frames=len(events), interval=200, blit=True, repeat=False)

plt.legend()
plt.tight_layout()
plt.show()
