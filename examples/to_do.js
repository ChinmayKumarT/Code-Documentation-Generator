class Task {
    constructor(description) {
      this.description = description;
      this.completed = false; // By default, the task is pending
    }
  
    // Mark task as completed
    markCompleted() {
      this.completed = true;
    }
  
    // Display the task with its index
    displayTask(index) {
      console.log(`${index + 1}. ${this.description} - ${this.completed ? 'Completed' : 'Pending'}`);
    }
  }
  
  class TodoList {
    constructor() {
      this.tasks = [];
    }
  
    // Add a new task
    addTask(taskDescription) {
      this.tasks.push(new Task(taskDescription));
    }
  
    // Mark a task as completed by its index
    completeTask(taskIndex) {
      if (taskIndex >= 0 && taskIndex < this.tasks.length) {
        this.tasks[taskIndex].markCompleted();
        return true;
      }
      return false;
    }
  
    // View all tasks
    viewTasks() {
      if (this.tasks.length === 0) {
        console.log("No tasks to show.");
      } else {
        console.log("\nTo-Do List:");
        this.tasks.forEach((task, index) => task.displayTask(index));
      }
    }
  
    // Get the number of tasks
    taskCount() {
      return this.tasks.length;
    }
  }
  
  function getUserChoice() {
    console.log("\nTo-Do List Manager");
    console.log("1. Add a task");
    console.log("2. Complete a task");
    console.log("3. View tasks");
    console.log("4. Exit");
  
    const choice = parseInt(prompt("\nChoose an option: "), 10);
    if (isNaN(choice)) {
      console.log("Invalid input, please enter a number.");
      return -1;
    }
    return choice;
  }
  
  function handleAddTask(todoList) {
    const taskDescription = prompt("\nEnter the task description: ");
    todoList.addTask(taskDescription);
    console.log("Task added successfully.");
  }
  
  function handleCompleteTask(todoList) {
    todoList.viewTasks();
    const taskIndex = parseInt(prompt("\nEnter the task number to mark as completed: "), 10) - 1;
    if (todoList.completeTask(taskIndex)) {
      console.log("Task marked as completed.");
    } else {
      console.log("Invalid task number.");
    }
  }
  
  function handleViewTasks(todoList) {
    todoList.viewTasks();
  }
  
  function runApp() {
    const todoList = new TodoList();
  
    while (true) {
      const userChoice = getUserChoice();
  
      switch (userChoice) {
        case 1:
          handleAddTask(todoList);
          break;
        case 2:
          handleCompleteTask(todoList);
          break;
        case 3:
          handleViewTasks(todoList);
          break;
        case 4:
          console.log("Goodbye!");
          return;
        default:
          console.log("Invalid choice, please try again.");
      }
    }
  }
  
  runApp();
  