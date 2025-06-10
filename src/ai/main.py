# import sys
# from argChecker import helper, inputCleaner


# def main():
#     args = sys.argv
    
#     helper(args)
#     config = inputCleaner(args)
#     return 0;

# if __name__ == "__main__":
#     main()

#!/usr/bin/env python3
import sys
from argChecker import helper, inputCleaner
from ai_controller import AIController

def main():
    args = sys.argv
    helper(args)
    config = inputCleaner(args)
    
    # Run the AI
    ai = AIController(config)
    return ai.run()

if __name__ == "__main__":
    sys.exit(main())