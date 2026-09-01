import java.util.ArrayList;
import java.util.Scanner;

class TodoList {
    private ArrayList<Task> tasks;

    public TodoList() {
        tasks = new ArrayList<>();
    }

    public void addTask(String taskDescription) {
        tasks.add(new Task(taskDescription));
    }

    public boolean completeTask(int taskIndex) {
        if (taskIndex >= 0 && taskIndex < tasks.size()) {
            tasks.get(taskIndex).setCompleted(true);
            return true;
        }
        return false;
    }

    public void viewTasks() {
        if (tasks.isEmpty()) {
            System.out.println("No tasks to show.");
            return;
        }

        System.out.println("\nTo-Do List:");
        for (int i = 0; i < tasks.size(); i++) {
            Task task = tasks.get(i);
            String status = task.isCompleted() ? "Completed" : "Pending";
            System.out.println((i + 1) + ". " + task.getDescription() + " - " + status);
        }
    }
}

class Task {
    private String description;
    private boolean completed;

    public Task(String description) {
        this.description = description;
        this.completed = false;
    }

    public String getDescription() {
        return description;
    }

    public boolean isCompleted() {
        return completed;
    }

    public void setCompleted(boolean completed) {
        this.completed = completed;
    }
}

public class TodoListManager {
    public static void main(String[] args) {
        Scanner scanner = new Scanner(System.in);
        TodoList todoList = new TodoList();

        while (true) {
            System.out.println("\nTo-Do List Manager");
            System.out.println("1. Add a task");
            System.out.println("2. Complete a task");
            System.out.println("3. View tasks");
            System.out.println("4. Exit");

            System.out.print("\nChoose an option: ");
            int choice;
            try {
                choice = Integer.parseInt(scanner.nextLine());
            } catch (NumberFormatException e) {
                System.out.println("Invalid input, please enter a number.");
                continue;
            }

            switch (choice) {
                case 1:
                    System.out.print("\nEnter the task description: ");
                    String taskDescription = scanner.nextLine();
                    todoList.addTask(taskDescription);
                    System.out.println("Task added successfully.");
                    break;

                case 2:
                    todoList.viewTasks();
                    System.out.print("\nEnter the task number to mark as completed: ");
                    int taskIndex;
                    try {
                        taskIndex = Integer.parseInt(scanner.nextLine()) - 1;
                        if (todoList.completeTask(taskIndex)) {
                            System.out.println("Task marked as completed.");
                        } else {
                            System.out.println("Invalid task number.");
                        }
                    } catch (NumberFormatException e) {
                        System.out.println("Invalid input, please enter a valid task number.");
                    }
                    break;

                case 3:
                    todoList.viewTasks();
                    break;

                case 4:
                    System.out.println("Goodbye!");
                    scanner.close();
                    return;

                default:
                    System.out.println("Invalid choice, please try again.");
            }
        }
    }
}
