from typing import Optional

class Task:
    def __init__(self, description: str) -> None:
        self.description: str = description
        self.completed: bool = False

    def __str__(self) -> str:
        """Returns a string representation of the task."""
        status: str = "Completed" if self.completed else "Pending"
        return f"{self.description} - {status}"


class TodoList:
    def __init__(self) -> None:
        self.tasks: list[Task] = []

    def add_task(self, task_description: str) -> None:
        """Adds a new task to the list."""
        self.tasks.append(Task(task_description))

    def complete_task(self, task_index: int) -> bool:
        """Marks a task as completed if index is valid. Returns a boolean."""
        if 0 <= task_index < len(self.tasks):
            self.tasks[task_index].completed = True
            return True
        return False

    def view_tasks(self) -> None:
        """Displays all tasks with their status."""
        if not self.tasks:
            print("No tasks to show.")
        else:
            print("\nTo-Do List:")
            for i, task in enumerate(self.tasks, start=1):
                print(f"{i}. {task}")


class TodoListManager:
    def __init__(self) -> None:
        self.todo_list: TodoList = TodoList()

    def get_user_choice(self) -> Optional[int]:
        """Gets user input for menu choice, returns an integer or None if invalid."""
        print("\nTo-Do List Manager")
        print("1. Add a task")
        print("2. Complete a task")
        print("3. View tasks")
        print("4. Exit")

        choice: str = input("\nChoose an option: ").strip()

        if choice.isdigit():
            return int(choice)
        else:
            print("Invalid input. Please enter a number.")
            return None

    def handle_add_task(self) -> None:
        """Handles adding a task."""
        task_description: str = input("\nEnter the task description: ").strip()
        self.todo_list.add_task(task_description)
        print("Task added successfully.")

    def handle_complete_task(self) -> None:
        """Handles marking a task as completed."""
        self.todo_list.view_tasks()
        try:
            task_index: int = int(input("\nEnter the task number to mark as completed: ")) - 1
            if self.todo_list.complete_task(task_index):
                print("Task marked as completed.")
            else:
                print("Invalid task number.")
        except ValueError:
            print("Invalid input, please enter a valid task number.")

    def handle_view_tasks(self) -> None:
        """Displays tasks."""
        self.todo_list.view_tasks()

    def run(self) -> None:
        """Main loop to run the Todo List manager."""
        while True:
            user_choice: Optional[int] = self.get_user_choice()

            if user_choice == 1:
                self.handle_add_task()
            elif user_choice == 2:
                self.handle_complete_task()
            elif user_choice == 3:
                self.handle_view_tasks()
            elif user_choice == 4:
                print("Goodbye!")
                break
            else:
                print("Invalid choice, please try again.")


if __name__ == "__main__":
    manager: TodoListManager = TodoListManager()
    manager.run()
