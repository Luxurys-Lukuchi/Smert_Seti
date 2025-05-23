import numpy as np
import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation
from collections import deque


def lambda_t(t):
    return 1 - 0.01 * np.abs(t - 70)


def mu_t(t):
    return max(0.01, 0.1 - 0.012 * np.abs(t - 50))



def simulate_smo_queue(T, lambda_max):
    t = 0
    queue = deque()
    service_busy = False
    service_end = 0
    served = 0
    arrived = 0
    total_wait_time = 0
    idle_time_start = 0
    total_idle_time = 0
    events = []
    queue_history = []

    while t <= T:

        u1 = np.random.uniform()
        arrival_time = t + (-np.log(u1) / lambda_max if u1 > 0 else 0)


        if service_busy:
            next_event = min(arrival_time, service_end) if arrival_time <= T else service_end
        else:
            next_event = arrival_time if arrival_time <= T else T + 1

        if next_event > T:
            break

        t = next_event

        if service_busy and t >= service_end:

            service_duration = t - service_end
            print(f"[{t:.2f}] Окончание обслуживания заявки. Длительность: {service_duration:.2f}")
            service_busy = False
            events.append((t, 'end', None))
            if queue:

                service_time = np.random.exponential(1 / mu_t(t))
                service_end = t + service_time
                service_busy = True
                served += 1
                events.append((t, 'start', service_end))
                queue.popleft()
                print(f"[{t:.2f}] Начало обслуживания заявки из очереди. Конец через {service_time:.2f}")

        if t == arrival_time and arrival_time <= T:

            current_lambda = lambda_t(t)
            u2 = np.random.uniform()
            if u2 <= current_lambda / lambda_max:
                arrived += 1
                print(f"[{t:.2f}] Пришла новая заявка.")
                if not service_busy:

                    service_time = np.random.exponential(1 / mu_t(t))
                    service_end = t + service_time
                    service_busy = True
                    served += 1
                    events.append((t, 'start', service_end))
                    print(f"[{t:.2f}] Начало обслуживания новой заявки. Конец через {service_time:.2f}")
                else:

                    queue.append(t)
                    events.append((t, 'enqueue', None))
                    print(f"[{t:.2f}] Заявка добавлена в очередь. Текущая длина очереди: {len(queue)}")


        if not service_busy:
            if idle_time_start == 0:
                idle_time_start = t
        else:
            if idle_time_start != 0:
                total_idle_time += t - idle_time_start
                idle_time_start = 0


        queue_history.append((t, len(queue), service_busy))

    return events, queue_history, served, arrived, total_idle_time


T = 100
lambda_max = max(lambda_t(t) for t in np.linspace(0, T, 1000))


events, queue_history, served, arrived, total_idle_time = simulate_smo_queue(T, lambda_max)


fig, ax2 = plt.subplots(figsize=(14, 5))
fig.suptitle('Моделирование СМО с ожиданием ', fontsize=16)


ax2.set_xlim(0, T)
max_queue = max(q[1] for q in queue_history)
ax2.set_ylim(0, max_queue + 1)
ax2.set_xlabel('Время')
ax2.set_ylabel('Длина очереди')
ax2.grid(True)


queue_line, = ax2.plot([], [], 'b-', lw=2, label='Длина очереди')
ax2.legend(loc='upper left')


time_points = []
queue_lengths = []



def init():
    queue_line.set_data([], [])
    return [queue_line]



def update(frame):
    t, q_len, _ = queue_history[frame]
    time_points.append(t)
    queue_lengths.append(q_len)


    queue_line.set_data(time_points, queue_lengths)

    return [queue_line]



ani = FuncAnimation(fig, update, frames=len(queue_history),
                    init_func=init, blit=True, interval=50, repeat=False)

plt.tight_layout()
plt.show()


print("\n=== Итоговые результаты ===")
print(f"Обслужено заявок: {served}")
print(f"Пришло заявок: {arrived}")
print(f"Отказов: {arrived - served}")
print(f"Средняя интенсивность потока: {arrived / T:.2f} заявок/ед. времени")
print(f"Среднее время простаивания системы: {total_idle_time / T:.2f} ед. времени")