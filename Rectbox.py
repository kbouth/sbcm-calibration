import matplotlib.pyplot as plt
import matplotlib.patches as patches
import matplotlib.animation as animation
import numpy as np

fig, ax = plt.subplots()

# Initial rectangle
rect = patches.Rectangle((0, 0), 1, 1, fill=False, edgecolor='red')
ax.add_patch(rect)

def animate(i):
    # Generate random data for the rectangle's position and size
    x = np.random.rand() * 5
    y = np.random.rand() * 5
    width = np.random.rand() * 2
    height = np.random.rand() * 2

    # Update the rectangle
    rect.set_xy((x, y))
    rect.set_width(width)
    rect.set_height(height)

    return rect,

# Create the animation
ani = animation.FuncAnimation(fig, animate, interval=100)

plt.xlim(0, 10)
plt.ylim(0, 10)
plt.show()
