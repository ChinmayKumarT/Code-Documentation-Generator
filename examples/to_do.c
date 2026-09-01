#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#define MAX_TASKS 100
#define MAX_DESC_LENGTH 256

// Structure to represent a Task
typedef struct {
    char description[MAX_DESC_LENGTH];
    int completed;  // 0 for pending, 1 for completed
} Task;

// Structure to represent the TodoList
typedef struct {
    Task tasks[MAX_TASKS];
    int task_count;
} TodoList;

// Function prototypes
void init_todolist(TodoList *todo_list);
void add_task(TodoList *todo_list, const char *task_description);
int complete_task(TodoList *todo_list, int task_index);
void view_tasks(TodoList *todo_list);
int get_user_choice();
void handle_add_task(TodoList *todo_list);
void handle_complete_task(TodoList *todo_list);
void handle_view_tasks(TodoList *todo_list);

int main() {
    TodoList todo_list;
    init_todolist(&todo_list);

    while (1) {
        int user_choice = get_user_choice();

        switch (user_choice) {
            case 1:
                handle_add_task(&todo_list);
                break;
            case 2:
                handle_complete_task(&todo_list);
                break;
            case 3:
                handle_view_tasks(&todo_list);
                break;
            case 4:
                printf("Goodbye!\n");
                return 0;
            default:
                printf("Invalid choice, please try again.\n");
        }
    }

    return 0;
}

// Function to initialize the TodoList
void init_todolist(TodoList *todo_list) {
    todo_list->task_count = 0;
}

// Function to add a task to the TodoList
void add_task(TodoList *todo_list, const char *task_description) {
    if (todo_list->task_count < MAX_TASKS) {
        strncpy(todo_list->tasks[todo_list->task_count].description, task_description, MAX_DESC_LENGTH);
        todo_list->tasks[todo_list->task_count].completed = 0; // Task is initially pending
        todo_list->task_count++;
        printf("Task added successfully.\n");
    } else {
        printf("Task list is full. Cannot add more tasks.\n");
    }
}

// Function to mark a task as completed
int complete_task(TodoList *todo_list, int task_index) {
    if (task_index >= 0 && task_index < todo_list->task_count) {
        todo_list->tasks[task_index].completed = 1;
        return 1;  // Task marked as completed successfully
    }
    return 0;  // Invalid task index
}

// Function to display all tasks in the TodoList
void view_tasks(TodoList *todo_list) {
    if (todo_list->task_count == 0) {
        printf("No tasks to show.\n");
    } else {
        printf("\nTo-Do List:\n");
        for (int i = 0; i < todo_list->task_count; i++) {
            printf("%d. %s - %s\n", i + 1, todo_list->tasks[i].description,
                   todo_list->tasks[i].completed ? "Completed" : "Pending");
        }
    }
}

// Function to get user choice from the menu
int get_user_choice() {
    int choice;
    printf("\nTo-Do List Manager\n");
    printf("1. Add a task\n");
    printf("2. Complete a task\n");
    printf("3. View tasks\n");
    printf("4. Exit\n");

    printf("\nChoose an option: ");
    if (scanf("%d", &choice) != 1) {
        // Clear the buffer in case of invalid input
        while (getchar() != '\n');
        printf("Invalid input, please enter a number.\n");
        return -1;
    }
    return choice;
}

// Function to handle adding a new task
void handle_add_task(TodoList *todo_list) {
    char task_description[MAX_DESC_LENGTH];
    printf("\nEnter the task description: ");
    getchar();  // to consume the leftover newline character from the previous input
    fgets(task_description, MAX_DESC_LENGTH, stdin);
    task_description[strcspn(task_description, "\n")] = '\0';  // Remove the newline at the end
    add_task(todo_list, task_description);
}

// Function to handle completing a task
void handle_complete_task(TodoList *todo_list) {
    view_tasks(todo_list);
    int task_index;
    printf("\nEnter the task number to mark as completed: ");
    if (scanf("%d", &task_index) != 1) {
        printf("Invalid input, please enter a valid task number.\n");
        return;
    }
    task_index--;  // Adjust for 0-based index
    if (complete_task(todo_list, task_index)) {
        printf("Task marked as completed.\n");
    } else {
        printf("Invalid task number.\n");
    }
}

// Function to handle viewing tasks
void handle_view_tasks(TodoList *todo_list) {
    view_tasks(todo_list);
}
