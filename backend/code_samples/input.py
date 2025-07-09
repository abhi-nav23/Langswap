def process_numbers(numbers):
    result = []
    for num in numbers:
        if num % 2 == 0:
            result.append(num * 2)  # Double even numbers
        else:
            result.append(num + 1)  # Increment odd numbers
    return result

# Sample list of integers
my_list = [1, 2, 3, 4, 5]

# Call the function and print the result
processed = process_numbers(my_list)
print("Processed list:", processed)