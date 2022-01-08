import numpy as np
import random
import time
import tkinter as tk


class SimulationResult:
    def __init__(self):
        self.sectionResultsList = []


class SectionResult:
    def __init__(self):
        self.stepsResultList = []


def mock_result():
    simulation_result = SimulationResult()
    nr_of_section = 5
    nr_of_steps = 5
    for i in range(nr_of_section):
        section_result = SectionResult()
        for j in range(nr_of_steps):
            section_result.stepsResultList.append(np.zeros((10, 8)))
        simulation_result.sectionResultsList.append(section_result)

    return simulation_result


class Section:
    """
  output[width] - indexes of next section lines
  """

    def __init__(self, section_type, length, width, output, narrowing):
        self.width = width
        self.road = np.ndarray((length, width), dtype=np.object)
        if (section_type == "start"):
            for col in range(length):
                for cell in range(width):
                    self.road[col][cell] = Agent(random.randint(1, 5), 1)
        else:
            for col in range(length):
                for cell in range(width):
                    self.road[col][cell] = Agent(random.randint(1, 5), 0)

        self.output = output
        self.length = length
        self.narrowing = narrowing
        self.section_type = section_type


class Agent:
    def __init__(self, max_velocity, agent_state):
        self.agent_state = agent_state  # 0 - empty road, 1 - runner
        self.velocity = 0
        self.max_velocity = max_velocity


changing_line_probability = 0.9
safety_look_back = 5


def random_change(route):
    for section in route:
        for col in section.road:
            for index, cell in enumerate(col):
                if cell.agent_state == 1 and random.uniform(0, 1) > changing_line_probability:
                    if section.section_type == "straight" or section.section_type == "start":
                        left_or_right = random.randint(0, 1)
                        if left_or_right == 0 and index > 0 and col[index - 1].agent_state == 0:
                            cell, col[index - 1] = col[index - 1], cell
                        elif left_or_right == 1 and index < section.width - 1 and col[index + 1].agent_state == 0:
                            cell, col[index + 1] = col[index + 1], cell
                    elif section.section_type == "bend_left" and index > 0 and col[index - 1].agent_state == 0:
                        cell, col[index - 1] = col[index - 1], cell
                    elif section.section_type == "bend_right" and index < section.width - 1 and col[index + 1].agent_state == 0:
                        cell, col[index + 1] = col[index + 1], cell


def beverage_dispensing_line_change(route):  # TODO
    return


def accelerate(route):
    for section in route:
        for col in section.road:
            for cell in col:
                if cell.velocity < cell.max_velocity:
                    cell.velocity += 1


# todo check 2nd line right and 2nd line left
def change_line(route):
    new_route = create_route()
    for section_index, section in enumerate(route):
        for col_index, col in enumerate(section.road):
            for cell_index, cell in enumerate(col):
                if cell.agent_state == 1:

                    agent_velocity = route[section_index].road[col_index][cell_index].velocity
                    agent_max_velocity = route[section_index].road[col_index][cell_index].max_velocity

                    if safety_look_back > col_index:
                        new_route[section_index].road[col_index][cell_index].agent_state = 1
                        new_route[section_index].road[col_index][cell_index].velocity = agent_velocity
                        new_route[section_index].road[col_index][cell_index].max_velocity = agent_max_velocity
                        continue

                    free_space_on_left = -1
                    free_space_on_right = -1
                    free_space = free_space_infront(route, section_index, cell_index, col_index)
                    if cell_index > 0:
                        if route[section_index].road[col_index][cell_index - 1].agent_state == 1:
                            free_space_on_left = -1
                        else:
                            free_space_on_left = free_space_infront(route, section_index, cell_index - 1, col_index)

                    if cell_index < section.width - 1:
                        if route[section_index].road[col_index][cell_index + 1].agent_state == 1:
                            free_space_on_right = -1
                        else:
                            free_space_on_right = free_space_infront(route, section_index, cell_index + 1, col_index)

                    can_change = True
                    if free_space_on_left > free_space_on_right and free_space_on_left > free_space:
                        for col_back in range(safety_look_back):
                            if section.road[col_index - col_back][cell_index - 1].agent_state == 1:
                                can_change = False
                                break
                        if can_change:
                            new_route[section_index].road[col_index][cell_index - 1].agent_state = 1
                            new_route[section_index].road[col_index][cell_index - 1].velocity = agent_velocity
                            new_route[section_index].road[col_index][cell_index - 1].max_velocity = agent_max_velocity

                    elif free_space_on_right > free_space_on_left and free_space_on_right > free_space:
                        for col_back in range(safety_look_back):
                            if section.road[col_index - col_back][cell_index + 1].agent_state == 1:
                                can_change = False
                                break
                        if can_change:
                            new_route[section_index].road[col_index][cell_index + 1].agent_state = 1
                            new_route[section_index].road[col_index][cell_index + 1].velocity = agent_velocity
                            new_route[section_index].road[col_index][cell_index + 1].max_velocity = agent_max_velocity
                    else:
                        new_route[section_index].road[col_index][cell_index].agent_state = 1
                        new_route[section_index].road[col_index][cell_index].velocity = agent_velocity
                        new_route[section_index].road[col_index][cell_index].max_velocity = agent_max_velocity
    return new_route


def avoid_crashes(route):
    for section_index, section in enumerate(route):
        for col_index, col in enumerate(section.road):
            for cell_index, cell in enumerate(col):
                if cell.agent_state == 1:
                    new_velocity = free_space_infront(route, section_index, cell_index, col_index)
                    cell.velocity = new_velocity


def free_space_infront(route, section_index, cell_index, col_index):
    i = 0
    next_col_index = col_index
    free_space = 0
    while i <= route[section_index].road[col_index][cell_index].velocity:
        next_col_index += 1
        if next_col_index < route[section_index].length:
            next_cell = route[section_index].road[next_col_index][cell_index]
            if next_cell.agent_state == 1:
                free_space = i
                break
        elif section_index + 1 < len(route) and not route[section_index].narrowing[cell_index]:
            next_cell = route[section_index + 1].road[next_col_index - route[section_index].length][
                route[section_index].output[cell_index]]
            if next_cell.agent_state == 1:
                free_space = i
                break
        elif section_index + 1 < len(route) and route[section_index].narrowing[cell_index]:
            free_space = i
            break
        elif section_index + 1 >= len(route):
            free_space = route[section_index].road[col_index][cell_index].velocity
            break
        free_space = i
        i += 1
    return free_space


def update(route):
    new_route = create_route()

    for section_index, section in enumerate(route):
        for col_index, col in enumerate(section.road):
            for cell_index, cell in enumerate(col):
                if cell.agent_state == 1:
                    new_col_index = col_index + cell.velocity
                    if new_col_index < section.length:
                        new_route[section_index].road[new_col_index][cell_index].agent_state = 1
                        new_route[section_index].road[new_col_index][cell_index].max_velocity = cell.max_velocity
                        new_route[section_index].road[new_col_index][cell_index].velocity = cell.velocity
                    elif new_col_index >= section.length and section_index + 1 < len(route):
                        new_col_index -= section.length

                        new_cell_index = section.output[cell_index]
                        new_route[section_index + 1].road[new_col_index][new_cell_index].agent_state = 1
                        new_route[section_index + 1].road[new_col_index][
                            new_cell_index].max_velocity = cell.max_velocity
                        new_route[section_index + 1].road[new_col_index][new_cell_index].velocity = cell.velocity
    return new_route


def show_section(section):
    # clear_output()
    for col in section.road:
        line = ""
        for cell in col:
            if cell.agent_state == 0:
                line += "_"
            else:
                line += "O"
        print(line)


def create_route():
    route = [Section("straight", 10, 5, [0, 0, 1, 2, 2], [True, False, False, False, True]),
             Section("straight", 20, 3, [1, 2, 3], [False, False, False]),
             Section("bend_right", 20, 5, [0, 1, 2, 3, 4], [True, False, False, False, True])]
    return route


def draw_canvas(step, simulation_result, section_nr, canvas_root, direction):
    for widget in canvas_root.winfo_children():
        if widget.widgetName == 'canvas':
            widget.destroy()

    if direction == "prev":
        step[0] -= 1
    elif direction == "next":
        step[0] += 1

    runners_count = 0
    steps_result = simulation_result.sectionResultsList[int(section_nr)].stepsResultList[step[0]]
    x, y = steps_result.shape
    for i in range(x):
        for j in range(y):
            if steps_result[i][j] == 0:
                canvas = tk.Canvas(canvas_root,
                                   bg="gray",
                                   width=15,
                                   height=15)
                canvas.grid(row=j, column=i)
            elif steps_result[i][j] == 1:
                runners_count += 1
                canvas = tk.Canvas(canvas_root,
                                   bg="red",
                                   width=15,
                                   height=15)
                canvas.grid(row=j, column=i)

    # Show number of runners and step
    label = tk.Label(canvas_root, text="Step " + str(step[0]), relief=tk.RAISED)
    label.grid(row=90, column=5, sticky=tk.W + tk.E, columnspan=5)
    label = tk.Label(canvas_root, text="Runners: " + str(runners_count), relief=tk.RAISED)
    label.grid(row=100, column=5, sticky=tk.W + tk.E, columnspan=5)


running = False


def play_pause():
    global running
    running = not running


def animate(step, simulation_result, section_nr, canvas_root):
    if running:  # Only do this if the Stop button has not been clicked
        draw_canvas(step, simulation_result, section_nr, canvas_root, "next")
        canvas_root.update()

    # After 1 second, call scanning again (create a recursive loop)
    root.after(1000, lambda: animate(step, simulation_result, section_nr, canvas_root))


def create_window(section_nr, simulation_result, my_route):
    canvas_root = tk.Tk()
    canvas_root.geometry("500x300")
    step = [0]
    nr_of_steps = len(simulation_result.sectionResultsList[0].stepsResultList) - 1
    draw_canvas(step, simulation_result, section_nr, canvas_root, "none")

    btn = tk.Button(canvas_root, text="PREV STEP", font="Sans-serif 10", bg="#3CB371",
                    command=lambda: draw_canvas(step, simulation_result, section_nr, canvas_root, "prev"))
    btn.grid(row=50, column=0, sticky=tk.W + tk.E, columnspan=5)

    btn = tk.Button(canvas_root, text="PLAY/PAUSE", font="Sans-serif 10", bg="#3CB371",
                    command=play_pause)
    btn.grid(row=50, column=5, sticky=tk.W + tk.E, columnspan=5)

    btn = tk.Button(canvas_root, text="NEXT STEP", font="Sans-serif 10", bg="#3CB371",
                    command=lambda: draw_canvas(step, simulation_result, section_nr, canvas_root, "next"))
    btn.grid(row=50, column=10, sticky=tk.W + tk.E, columnspan=5)

    # Show section info
    l1 = tk.Label(canvas_root)  # empty row as margin-top
    l1.grid(row=60, column=1, sticky=tk.W + tk.E, columnspan=5)

    section_name = my_route[int(section_nr)].section_type.upper() + " SECTION"
    label = tk.Label(canvas_root, text=section_name, relief=tk.RAISED)
    label.grid(row=80, column=5, sticky=tk.W + tk.E, columnspan=5)

    canvas_root.after(1000, lambda: animate(step, simulation_result, section_nr, canvas_root))
    canvas_root.mainloop()


def create_widgets(result, my_route):
    parent = tk.Tk()
    parent.geometry("300x100")
    l1 = tk.Label(parent, text="Section : ", font="Sans-serif 14", bg="#B0C4DE", bd=1,
                  relief=tk.RAISED)  # Main Window
    l1.grid(row=0, column=0, sticky=tk.W + tk.E)

    variable = tk.StringVar(parent)
    variable.set("0")  # default value
    result_indexes = []
    for i, _ in enumerate(result.sectionResultsList):
        result_indexes.append(str(i))
    menu = tk.OptionMenu(parent, variable, *result_indexes)

    menu.grid(row=0, column=1, sticky=tk.W + tk.E)

    btn = tk.Button(parent, text=" OK ", font="Sans-serif 10", bg="#3CB371",  # OK Button
                    command=lambda: create_window(variable.get(), result, my_route), pady=0)
    btn.grid(row=5, column=0, sticky=tk.W + tk.E, columnspan=2)
    return parent


def run_simulation(my_route):
    simulation_result = SimulationResult()

    for section in my_route:
        simulation_result.sectionResultsList.append(SectionResult())

    for step in range(50):
        # clear = "\n" * 100
        # print(clear)
        # clear_output()
        # for i, section in enumerate(my_route):
        #     if i == 0:
        #         show_section(section)
        #     else:
        #         show_section(section)

        accelerate(my_route)
        random_change(my_route)
        my_route = change_line(my_route)
        avoid_crashes(my_route)
        my_route = update(my_route)

        for section_index, section in enumerate(my_route):
            simulation_result.sectionResultsList[section_index].stepsResultList.append(
                np.zeros((section.length, section.width)))
            for col_index, col in enumerate(section.road):
                for cell_index, cell in enumerate(col):
                    if cell.agent_state == 1:
                        simulation_result.sectionResultsList[section_index].stepsResultList[step][col_index][
                            cell_index] = 1

    return simulation_result


init_route = [Section("start", 10, 5, [0, 0, 1, 2, 2], [True, False, False, False, True]),
              Section("straight", 20, 3, [0, 1, 2], [False, False, False]),
              Section("bend_right", 20, 5, [0, 1, 2, 3, 4], [True, False, False, False, True])
              ]

result = run_simulation(init_route)
root = create_widgets(result, init_route)
root.mainloop()
