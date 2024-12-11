from textx import metamodel_from_file
import threading
import random


class EduLangInterpreter:

    def __init__(self):
        # Store categories, each containing definitions, quizzes, and hints
        self.categories = {}
        self.timer = None
        self.incorrect_limit = 2  # Default value if not set
        self.variables = {}  # Store variables
        self.score = 0  # Initialize score
        self.total_attempts = 0  # Total questions attempted


    def interpret(self, model):
        # Process the timer declaration
        if model.timer:
            self.timer = model.timer.value

        # Process the incorrect limit declaration
        if model.incorrect:
            self.incorrect_limit = model.incorrect.value

        # Process variable declarations
        for variable in model.variables:
            self.variables[variable.name] = variable.value

        # Process commands
        if model.commands:
            for command in model.commands:
                if command == "showScore":
                    print(f"Your current score is: {self.score}")
                elif command == "resetScore":
                    self.score = 0
                    print("Score has been reset.")

        # Process each category in the program
        for category in model.categories:
            category_name = category.name
            self.categories[category_name] = {
                "definitions": {},
                "quizzes": [],
                "hints": {}
            }

            current_quiz = None
            for statement in category.statements:
                if statement.__class__.__name__ == "Define":
                    # Resolve variables in definitions
                    resolved_definition = self.resolve_value(
                        statement.definition)
                    self.categories[category_name]["definitions"][statement.term] = resolved_definition

                elif statement.__class__.__name__ == "Quiz":
                    # Resolve each answer in the AnswerList
                    resolved_answers = [self.resolve_value(
                        ans) for ans in statement.answers.elements]
                    self.categories[category_name]["quizzes"].append(
                        (statement.question, resolved_answers))
                    current_quiz = statement.question
                    self.categories[category_name]["hints"][current_quiz] = []

                elif statement.__class__.__name__ == "Hint":
                    if current_quiz:
                        self.categories[category_name]["hints"][current_quiz].append(
                            statement.text)

                elif statement.__class__.__name__ == "Comment":
                    # Ignore comments
                    pass

    def resolve_value(self, value):
        if isinstance(value, str):  # If it's a plain string
            return value
        elif value.__class__.__name__ == "Reference":  # If it's a variable reference
            var_name = value.name
            if var_name in self.variables:
                return self.variables[var_name]
            else:
                raise ValueError(f"Variable '{var_name}' is not defined.")
        else:
            raise ValueError(f"Unsupported value type: {value}")

    def run(self):
        while True:
            print("\nMain Menu:")
            print("1. View Categories")
            print("2. Show Score")
            print("3. Reset Score")
            print("4. Exit")
            choice = input("Choose an option: ")

            if choice == "1":
                self.display_categories()
            elif choice == "2":
                if self.total_attempts > 0:
                    percentage = (self.score / self.total_attempts) * 100
                    print(f"Your current score is: {self.score}/{self.total_attempts} ({percentage:.2f}%)")
                else:
                    print("No questions attempted yet.")
            elif choice == "3":
                self.score = 0
                self.total_attempts = 0
                print("Score and attempts have been reset.")
            elif choice == "4":
                print("Exiting program. Goodbye!")
                break
            else:
                print("Invalid option. Please try again.")


    def display_categories(self):
        print("\nCategories:")
        for i, category_name in enumerate(self.categories.keys(), start=1):
            print(f"{i}. {category_name}")
        choice = input("Choose a category or type 'back' to return: ")

        if choice.isdigit():
            choice = int(choice)
            if 1 <= choice <= len(self.categories):
                category_name = list(self.categories.keys())[choice - 1]
                self.display_category_menu(category_name)
        elif choice.lower() == "back":
            return
        else:
            print("Invalid choice.")

    def display_category_menu(self, category_name):
        while True:  # Loop to stay in the category menu
            print(f"\n{category_name} Menu:")
            print("1. View Definitions")
            print("2. Test All Quizzes")
            print("3. Choose a Quiz")
            print("4. Back to Categories")
            choice = input("Choose an option: ")

            if choice == "1":
                self.display_definitions(category_name)
            elif choice == "2":
                self.test_all_quizzes(category_name)
            elif choice == "3":
                self.choose_quiz(category_name)
            elif choice == "4":
                return  # Exit the category menu loop
            else:
                print("Invalid option. Please try again.")

    def display_definitions(self, category_name):
        print("\nDefinitions:")
        for term, definition in self.categories[category_name]["definitions"].items():
            print(f"- {term}: {definition}")

    def test_all_quizzes(self, category_name):
        quizzes = self.categories[category_name]["quizzes"]
        random.shuffle(quizzes)  # Shuffle the quizzes to randomize their order

        for question, answer in quizzes:
            should_exit = self.ask_quiz(category_name, question, answer)
            if should_exit:
                print("Exiting test early...")
                break  # Stop the loop if the user chooses to exit

    def choose_quiz(self, category_name):
        print("\nQuizzes:")
        for i, (question, _) in enumerate(self.categories[category_name]["quizzes"], start=1):
            print(f"{i}. {question}")
        choice = input(
            "Type the number of a quiz to try it or 'back' to return: ")

        if choice.isdigit():
            choice = int(choice)
            if 1 <= choice <= len(self.categories[category_name]["quizzes"]):
                question, answer = self.categories[category_name]["quizzes"][choice - 1]
                self.ask_quiz(category_name, question, answer)
        elif choice.lower() == "back":
            return
        else:
            print("Invalid choice.")

    def ask_quiz(self, category_name, question, answers):
        print(f"\nQuiz: {question}")
        result = {"answered": False, "user_input": None}

        def time_out():
            if not result["answered"]:
                print("\nTime's up!")
                print(f"The correct answer(s) are: {', '.join(answers)}")
                result["answered"] = True

        if self.timer:
            timer_thread = threading.Timer(self.timer, time_out)
            timer_thread.start()

        attempts = self.incorrect_limit
        while attempts > 0 and not result["answered"]:
            user_input = input(
                "Your Answer (or type 'hint' or 'EXIT' to return to menu): ")

            if user_input.lower() == "exit":
                print("Returning to the menu...")
                result["answered"] = True
                if self.timer:
                    timer_thread.cancel()
                return True

            if user_input.lower() == "hint":
                hints = self.categories[category_name]["hints"].get(question, [])
                if hints:
                    print(f"Hint: {hints.pop(0)}")
                else:
                    print("No more hints available.")
            elif user_input.strip() in answers:
                print("Correct!")
                self.score += 1  # Increment correct answers
                self.total_attempts += 1  # Increment total attempts
                result["answered"] = True
                if self.timer:
                    timer_thread.cancel()
                return False
            else:
                attempts -= 1
                print(f"Incorrect. {attempts} attempts left.")

        if not result["answered"]:
            print(f"The correct answer(s) are: {', '.join(answers)}")
            self.total_attempts += 1  # Increment total attempts for incorrect answers
            result["answered"] = True
            if self.timer:
                timer_thread.cancel()

        return False



# Grammar for EduLang
edu_mm = metamodel_from_file('edulang.tx')

# Load and parse the EduLang program
edu_program = edu_mm.model_from_file('test_program.edulang')

# Create an interpreter instance and execute the program
interpreter = EduLangInterpreter()
interpreter.interpret(edu_program)
interpreter.run()
