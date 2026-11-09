import json
import os
from pathlib import Path

BASE_DIRECTORY = Path(__file__).resolve().parent
CONFIG_DIRECTORY = BASE_DIRECTORY / "config"
RECORD_DIRECTORY = BASE_DIRECTORY / "records"


# BASE LEVEL - these functions calculate and RETURN a result (they do not print).
def calories_per_minute(calories, duration):
    return round(float(calories) / duration, 1)


def get_intensity(rate):
    if rate < 5.0:
        return "Low"
    elif rate < 10.0:
        return "Moderate"
    else:
        return "High"


# INTERMEDIATE LEVEL - the total and maximum are determined by our own loops.
def calculate_total(values):
    total = 0
    for value in values:
        total += value
    return total


def calculate_average(values):
    if len(values) == 0:
        return 0.0
    return round(calculate_total(values) / len(values), 1)


def find_best_workout(names, calories_list):
    if len(names) == 0:
        return "None"

    best_index = 0
    for index in range(1, len(calories_list)):
        if calories_list[index] > calories_list[best_index]:
            best_index = index
    return names[best_index]


# SELECTED ADVANCED FEATURES - functions are combined to produce reports.
def check_goal(total_calories, goal):
    if total_calories >= goal:
        return f"Goal reached! You burned {total_calories:g} calories."
    else:
        return f"{goal - total_calories:g} calories short of your {goal}-calorie goal."


def format_workout_row(name, duration, calories, width=20):
    rate = calories_per_minute(calories, duration)
    intensity = get_intensity(rate)
    return (f"{name:<{width}}  {duration:>8g}  {calories:>8g}  "
            f"{rate:>7.1f} c/m  {intensity}")


def workout_table(names, durations, calories_list, heading):
    width = 20
    for name in names:
        if len(name) > width:
            width = len(name)

    lines = [
        heading,
        f"{'Workout':<{width}}  {'Duration':>8}  {'Calories':>8}  {'Rate':>11}  Intensity",
        "-" * (width + 45),
    ]

    for index in range(len(names)):
        lines.append(format_workout_row(
            names[index], durations[index], calories_list[index], width
        ))
    return "\n".join(lines)


def print_workout_table(names, durations, calories_list):
    width = 20
    for name in names:
        if len(name) > width:
            width = len(name)

    print(f"{'Workout':<{width}}  {'Duration':>8}  {'Calories':>8}  {'Rate':>11}  Intensity")
    print("-" * (width + 45))
    for index in range(len(names)):
        print(format_workout_row(names[index], durations[index], calories_list[index], width))


def session_summary(names, durations, calories_list, goal):
    if len(names) == 0:
        return "No workouts were logged. Session summary skipped."

    total_calories = calculate_total(calories_list)
    return "\n".join([
        "===== Session Summary ==================================================",
        f"{'Workouts logged':<20}: {len(names)}",
        f"{'Total calories':<20}: {total_calories:g}",
        f"{'Avg calories':<20}: {calculate_average(calories_list):.1f}",
        f"{'Total duration':<20}: {calculate_total(durations):g} min",
        f"{'Avg duration':<20}: {calculate_average(durations):.1f} min",
        f"{'Best workout':<20}: {find_best_workout(names, calories_list)}",
        f"{'Goal check':<20}: {check_goal(total_calories, goal)}",
        "=======================================================================",
    ])


class Workout:

    def __init__(self, name, duration=None, calories=None):
        self.name = name.strip()
        self.duration = duration
        self.calories = calories

    def to_dict(self):
        return {
            "name": self.name,
            "duration": self.duration,
            "calories": self.calories,
        }


class FitnessRecord:

    def __init__(self, name="", goal=0, workouts=None, path=None):
        self.name = name
        self.goal = goal
        self.workouts = workouts if workouts is not None else []
        self.path = path

    def save(self):
        workouts_data = []
        for workout in self.workouts:
            workouts_data.append(workout.to_dict())

        data = {
            "name": self.name,
            "goal": self.goal,
            "workouts": workouts_data,
        }
        with self.path.open("w", encoding="utf-8") as file:
            json.dump(data, file, indent=4)

    def load(self):
        with self.path.open("r", encoding="utf-8") as file:
            data = json.load(file)

        name = data["name"]
        goal = data["goal"]
        items = data["workouts"]

        if not isinstance(name, str) or not name.strip():
            raise ValueError("Invalid name in saved collection.")
        if type(goal) is not int or goal < 0:
            raise ValueError("Invalid calorie goal in saved collection.")
        if not isinstance(items, list) or len(items) == 0:
            raise ValueError("Collection must contain at least one workout.")

        workouts = []
        for item in items:
            workout_name = item["name"]
            duration = item.get("duration")
            calories = item.get("calories")
            if not isinstance(workout_name, str) or not workout_name.strip():
                raise ValueError("Invalid workout name in saved collection.")
            if (duration is None) != (calories is None):
                raise ValueError("A saved workout has incomplete results.")
            if duration is not None:
                if type(duration) not in (int, float) or duration <= 0:
                    raise ValueError("Invalid workout duration in saved collection.")
                if type(calories) not in (int, float) or calories < 0:
                    raise ValueError("Invalid calories in saved collection.")
            workouts.append(Workout(workout_name, duration, calories))

        self.name = name
        self.goal = goal
        self.workouts = workouts

    def complete(self):
        if not self.workouts:
            return False
        for workout in self.workouts:
            if workout.duration is None or workout.calories is None:
                return False
        return True

    def parallel_lists(self):
        names = []
        durations = []
        calories_list = []
        for workout in self.workouts:
            names.append(workout.name)
            durations.append(workout.duration)
            calories_list.append(workout.calories)
        return names, durations, calories_list


class FitnessTracker:

    def __init__(self):
        self.record = None
        self.entering_workouts = False
        self.collection_in_progress = False
        self.tools_enabled = False
        RECORD_DIRECTORY.mkdir(exist_ok=True)

    def clear_screen(self):
        if os.isatty(1):
            os.system("cls" if os.name == "nt" else "clear")

    def show_header(self):
        print("\n---[PERSONAL FITNESS TRACKER]-------------------------------------------")
        print("Commands: Help | Instr | Home | Exit")
        if (self.tools_enabled and self.record is not None and self.record.complete()
                and not self.entering_workouts and not self.collection_in_progress):
            print("Tools: anawk | summary | genrpt")
        print("------------------------------------------------------------------------")

    def help(self):
        path = CONFIG_DIRECTORY / "fitness_tools.json"
        try:
            with path.open("r", encoding="utf-8") as file:
                tools = json.load(file)
            if not isinstance(tools, list):
                raise ValueError("Expected a list of application tools.")
            print("\nHELP - APPLICATION TOOLS")
            for tool in tools:
                print(f"\n{tool['command']} - {tool['description']}")
                print(f"How to use: {tool['usage']}")
        except (OSError, ValueError, KeyError, TypeError) as error:
            print(f"File failed to load: {path} ({error})")

    def instructions(self):
        path = CONFIG_DIRECTORY / "instruction.txt"
        try:
            with path.open("r", encoding="utf-8") as file:
                print("\n" + file.read())
        except (OSError, UnicodeError) as error:
            print(f"File failed to load: {path} ({error})")

    def prompt(self, message, workout_name=None, show_header=True):
        while True:
            if show_header:
                self.show_header()

            # The workout name is repeated before BOTH fields, including retries.
            if workout_name is not None:
                print(f"===> {workout_name}")

            answer = input(message).strip()
            command = answer.lower().replace(" ", "")

            if command == "home":
                self.clear_screen()
                return None
            elif command == "exit":
                print("Goodbye!")
                raise SystemExit(0)
            elif command == "help":
                self.help()
            elif command == "instr":
                self.instructions()
            elif command in ("anawk", "summary", "anasum", "genrpt", "genrpt()"):
                if not self.tools_enabled:
                    print("Analysis tools are available after entering a complete collection. "
                          "Choose option 3 to continue a logged record.")
                elif command == "anawk":
                    self.analyze_workouts()
                elif command in ("summary", "anasum"):
                    self.show_summary()
                else:
                    self.generate_report()
            else:
                return answer

            # Restore the header after a help or report command.
            show_header = True

    def prompt_number(self, message, allow_zero=False, workout_name=None):
        while True:
            answer = self.prompt(message, workout_name)
            if answer is None:
                return None
            try:
                number = int(answer)
            except ValueError:
                print("Enter a whole number.")
                continue
            if number < 0 or (number == 0 and not allow_zero):
                print("Enter a whole number greater than zero."
                      if not allow_zero else "Enter a nonnegative whole number.")
                continue
            return number

    def valid_collection_name(self, name):
        if not name or name in (".", "..") or name.endswith((".", " ")):
            return False
        for character in name:
            if character in '<>:"/\\|?*' or ord(character) < 32:
                return False
        base_name = name.split(".")[0].upper()
        if base_name in ("CON", "PRN", "AUX", "NUL"):
            return False
        for number in range(1, 10):
            if base_name in (f"COM{number}", f"LPT{number}"):
                return False
        return True

    def load_workout_catalog(self):
        path = CONFIG_DIRECTORY / "workout_list.json"
        with path.open("r", encoding="utf-8") as file:
            items = json.load(file)
        if not isinstance(items, list) or len(items) == 0:
            raise ValueError("workout_list.json must contain a nonempty list.")

        catalog = []
        for item in items:
            if not isinstance(item, dict):
                raise ValueError("Workout entries must be JSON objects.")
            name = item["name"]
            if not isinstance(name, str) or not name.strip():
                raise ValueError("Each workout must have a name.")
            # A nested loop checks names without a replacement lookup function.
            for existing in catalog:
                if existing.lower() == name.strip().lower():
                    raise ValueError("Workout names must be unique.")
            catalog.append(name.strip())
        return catalog

    def new_collection(self):
        self.collection_in_progress = True
        try:
            return self._new_collection()
        finally:
            self.collection_in_progress = False

    def _new_collection(self):
        try:
            catalog = self.load_workout_catalog()
        except (OSError, ValueError, KeyError, TypeError) as error:
            print(f"File failed to load: {CONFIG_DIRECTORY / 'workout_list.json'} ({error})")
            return False

        goal = self.prompt_number("Daily Calorie Goal (whole number): ")
        if goal is None:
            return False
        name = self.prompt("Name: ")
        if name is None:
            return False
        name = name.strip().title()
        if not self.valid_collection_name(name):
            print("Enter a valid name that can be used as a filename.")
            return False

        path = RECORD_DIRECTORY / f"{name}_wk_Coll.json"
        for existing in RECORD_DIRECTORY.glob("*_wk_Coll.json"):
            if existing.name.lower() == path.name.lower():
                print("That collection already exists. Load it or enter another name.")
                return False

        selected = []
        print("\nAVAILABLE WORKOUTS - config/workout_list.json")
        while True:
            print(f"{'Index':<6} | Workout")
            print("-" * 35)
            for index, workout_name in enumerate(catalog, 1):
                marker = " (selected)" if workout_name in selected else ""
                print(f"{index:<6} | {workout_name}{marker}")

            choice = self.prompt("Workout index (done when finished): ")
            if choice is None:
                return False
            if choice.lower() in ("done", "/done"):
                if not selected:
                    print("No workouts were logged. No collection was saved.")
                    return False
                break
            if not choice.isdecimal() or not 1 <= int(choice) <= len(catalog):
                print("Enter a displayed workout index or done.")
                continue
            workout_name = catalog[int(choice) - 1]
            if workout_name in selected:
                print("That workout is already selected.")
                continue
            selected.append(workout_name)
            print(f"Selected: {workout_name}")

        # Match Week 2: save selected items BEFORE entering their measurements.
        record = FitnessRecord(name, goal, [Workout(item) for item in selected], path)
        record.save()
        print(f"Saved {len(selected)} workouts in records/{path.name}.")

        if self.enter_workout_results(record):
            self.record = record
            return True
        return False

    def load_collection(self):
        self.collection_in_progress = True
        try:
            return self._load_collection()
        finally:
            self.collection_in_progress = False

    def _load_collection(self):
        paths = sorted(RECORD_DIRECTORY.glob("*_wk_Coll.json"))
        if len(paths) == 0:
            print("No saved workout collections found in records.")
            return False

        print("\nSAVED COLLECTIONS")
        for index, path in enumerate(paths, 1):
            print(f"{index:>3} | {path.name}")
        while True:
            choice = self.prompt("Collection index: ")
            if choice is None:
                return False
            if choice.isdecimal() and 1 <= int(choice) <= len(paths):
                break
            print("Enter a displayed collection index.")

        record = FitnessRecord(path=paths[int(choice) - 1])
        try:
            record.load()
        except (OSError, ValueError, KeyError, TypeError) as error:
            print(f"File failed to load: {record.path} ({error})")
            return False

        print(f"Loaded collection: {record.name}")
        # A fresh goal is requested each time a collection is loaded.
        goal = self.prompt_number("Daily Calorie Goal (whole number): ")
        if goal is None:
            return False
        record.goal = goal

        if self.enter_workout_results(record):
            self.record = record
            return True
        return False

    def enter_workout_results(self, record):
        if len(record.workouts) == 0:
            print("No workouts were selected.")
            return False

        self.entering_workouts = True
        staged = []
        try:
            print("\nWelcome to the Personal Fitness Tracker!")
            print(f"You will log {len(record.workouts)} workouts.")

            for index, workout in enumerate(record.workouts, 1):
                print(f"\n--- {index}-({workout.name}) ---")
                print(f"Workout name: {workout.name}")
                duration = self.prompt_number(
                    "Duration (minutes): ", workout_name=workout.name
                )
                if duration is None:
                    print("Entry cancelled. Previous results were not changed.")
                    return False

                calories = self.prompt_number(
                    "Calories burned: ", allow_zero=True, workout_name=workout.name
                )
                if calories is None:
                    print("Entry cancelled. Previous results were not changed.")
                    return False

                staged.append(Workout(workout.name, duration, calories))
                rate = calories_per_minute(calories, duration)
                intensity = get_intensity(rate)
                print(f"Result: {workout.name} | {duration} min | {calories} cal | "
                      f"{rate:.1f} cal/min | Intensity: {intensity}")

            # Save only after every selected workout has both values entered.
            record.workouts = staged
            record.save()
            return True
        finally:
            self.entering_workouts = False

    def ready(self):
        if (self.record is None or not self.record.complete()
                or self.entering_workouts or self.collection_in_progress):
            print("Cannot display reports: complete or load workout results first.")
            return False
        return True

    def workout_details(self):
        record = self.record
        lines = [
            "Welcome to the Personal Fitness Tracker!",
            f"You will log {len(record.workouts)} workouts.",
        ]
        for index, workout in enumerate(record.workouts, 1):
            rate = calories_per_minute(workout.calories, workout.duration)
            intensity = get_intensity(rate)
            lines.extend([
                "",
                f"===[ {index} {workout.name} ]".ljust(75, "="),
                f"{'Workout name:':<26}| {workout.name}",
                f"{'Duration (minutes):':<26}| {workout.duration:g}",
                f"{'Calories burned:':<26}| {workout.calories:g}",
                f"Result: {workout.name} | {workout.duration:g} min | "
                f"{workout.calories:g} cal | {rate:.1f} cal/min | Intensity: {intensity}",
                "=" * 75,
            ])
        lines.append("All workouts logged. Great job staying active!\n"
                     "=>> Please select one of the tools above to analyse your workout.")
        return "\n".join(lines)

    def workout_heading(self):
        return f"===== {self.record.name} Workout Summary ".ljust(75, "=")

    def full_summary(self):
        record = self.record
        names, durations, calories_list = record.parallel_lists()
        return "\n\n".join([
            workout_table(names, durations, calories_list, self.workout_heading()),
            session_summary(names, durations, calories_list, record.goal),
        ])

    def analyze_workouts(self):
        if self.ready():
            self.clear_screen()
            print(self.workout_details())

    def show_summary(self):
        if self.ready():
            self.clear_screen()
            names, durations, calories_list = self.record.parallel_lists()
            print(self.workout_heading())
            print_workout_table(names, durations, calories_list)
            print("\n" + session_summary(names, durations, calories_list, self.record.goal))

    def generate_report(self):
        if not self.ready():
            return
        report_text = "\n\n".join([self.workout_details(), self.full_summary()])
        path = BASE_DIRECTORY / f"{self.record.name}_wk_report.txt"
        try:
            with path.open("w", encoding="utf-8") as file:
                file.write(report_text + "\n")
            print(f"Success: both reports saved to {path.name}")
        except OSError as error:
            print(f"Report file failed to save: {path} ({error})")

    def command_mode(self, just_completed=False):
        self.tools_enabled = True
        try:
            self.clear_screen()
            self.show_header()
            if just_completed:
                print("\nAll workouts logged. Great job staying active!\n"
                      "=>> Please select one of the tools above to analyse your workout.\n")

            first_prompt = True
            while True:
                # The header was already displayed at entry; do not duplicate it.
                answer = self.prompt("Enter command: ", show_header=not first_prompt)
                first_prompt = False
                if answer is None:  # Home clears the screen and returns to main menu.
                    return
                print("Choose anawk, summary, genrpt, Home, Help, Instr, or Exit.")
        finally:
            # Main menu shows commands only. Option 3 reopens analysis tools.
            self.tools_enabled = False

    def run(self):
        while True:
            print("\nWelcome to the Personal Fitness Tracker!")
            print("PERSONAL FITNESS TRACKER")
            print("1 - Load Collection")
            print("2 - Enter New Collection")
            if self.record is not None and self.record.complete():
                print("3 - Continue with logged record")

            choice = self.prompt("Select an option: ")
            if choice is None:
                continue
            if choice == "1":
                if self.load_collection():
                    self.command_mode(just_completed=True)
            elif choice == "2":
                if self.new_collection():
                    self.command_mode(just_completed=True)
            elif choice == "3" and self.record is not None and self.record.complete():
                self.command_mode()
            else:
                print("Choose an available menu option, or enter a displayed command.")


# Run the program only when this file is executed directly.
if __name__ == "__main__":
    try:
        FitnessTracker().run()
    except (EOFError, KeyboardInterrupt):
        print("\nGoodbye! Unfinished workout entries have not been saved.")
    except (OSError, ValueError, KeyError, TypeError) as error:
        print(f"Unable to continue: {error}")
