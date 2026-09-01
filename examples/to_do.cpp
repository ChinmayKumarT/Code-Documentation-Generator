#include <iostream>
#include <string>
#include <vector>

#define MAX_DESC_LENGTH 256

// Class to represent a Task
class Task {
private:
    std::string description;
    bool completed;  // true for completed, false for pending

public:
    Task(const std::string& desc) : description(desc), completed(false) {}

    std::string getDescription() const { return description; }
    bool isCompleted() const { return completed; }

    void markCompleted() { completed = true; }

    void displayTask(int index) const {
        std::cout << index + 1 << ". " << description 
                  << " - " << (completed ? "Completed" : "Pending") << std::endl;
    }
};

// Class to represent the TodoList
class TodoList {
private:
    std::vector<Task> tasks;

public:
    void addTask(const std::string& task_description) {
        tasks.push_back(Task(task_description));
    }

    bool completeTask(int task_index) {
        if (task_index >= 0 && task_index < tasks.size()) {
            tasks[task_index].markCompleted();
            return true;
        }
        return false;
    }

    void viewTasks() const {
        if (tasks.empty()) {
            std::cout << "No tasks to show." << std::endl;
        } else {
            std::cout << "\nTo-Do List:" << std::endl;
            for (size_t i = 0; i < tasks.size(); ++i) {
                tasks[i].displayTask(i);
            }
        }
    }

    size_t taskCount() const { return tasks.size(); }
};

// Function to get user choice for the menu
int getUserChoice() {
    int choice;
    std::cout << "\nTo-Do List Manager" << std::endl;
    std::cout << "1. Add a task" << std::endl;
    std::cout << "2. Complete a task" << std::endl;
    std::cout << "3. View tasks" << std::endl;
    std::cout << "4. Exit" << std::endl;

    std::cout << "\nChoose an option: ";
    std::cin >> choice;

    if (std::cin.fail()) {
        std::cin.clear(); // clear error flag
        std::cin.ignore(std::numeric_limits<std::streamsize>::max(), '\n'); // discard invalid input
        std::cout << "Invalid input, please enter a number." << std::endl;
        return -1;
    }
    return choice;
}

// Function to handle adding a new task
void handleAddTask(TodoList& todo_list) {
    std::string task_description;
    std::cout << "\nEnter the task description: ";
    std::cin.ignore();  // to clear the newline left by previous input
    std::getline(std::cin, task_description);
    todo_list.addTask(task_description);
    std::cout << "Task added successfully." << std::endl;
}

// Function to handle completing a task
void handleCompleteTask(TodoList& todo_list) {
    todo_list.viewTasks();
    int task_index;
    std::cout << "\nEnter the task number to mark as completed: ";
    std::cin >> task_index;
    task_index--;  // Adjusting for 0-based indexing

    if (todo_list.completeTask(task_index)) {
        std::cout << "Task marked as completed." << std::endl;
    } else {
        std::cout << "Invalid task number." << std::endl;
    }
}

// Function to handle viewing all tasks
void handleViewTasks(const TodoList& todo_list) {
    todo_list.viewTasks();
}

int main() {
    TodoList todo_list;

    while (true) {
        int user_choice = getUserChoice();

        switch (user_choice) {
            case 1:
                handleAddTask(todo_list);
                break;
            case 2:
                handleCompleteTask(todo_list);
                break;
            case 3:
                handleViewTasks(todo_list);
                break;
            case 4:
                std::cout << "Goodbye!" << std::endl;
                return 0;
            default:
                std::cout << "Invalid choice, please try again." << std::endl;
        }
    }

    return 0;
}
