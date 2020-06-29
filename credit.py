# from cs50 import get_string
# from cs50 import get_int

#American Express Master Card Visa

"""
1. multiply every other digit by two starting with the number's second-to-last digit, and then add those products together.
2. add the sum to the sum of the digits that weren't multiplied by 1
3. If the total's last digit is 0 (if the total modulo 10 is congruent to 0) the number is valid!
"""

def credit_validation(card_num):


    #card_num = get_int("Number: ")
    card_num_string = str(card_num)

    #1.

    sum_of_digits = 0;
    total_sum = 0;

    card_num_len = len(card_num_string)

    #print("length: ",card_num_len)


    myString = ""
    for i in range(0, card_num_len - 1, 2):
        #print(card_num_string[card_num_len - i - 2])

        myString = myString + card_num_string[card_num_len - i - 2]

        #print(int(card_num_string[card_num_len - i - 2]) * 2)

        #we need to add the sum of the digits

    #print(myString)

    newString = ""

    for i in range(len(myString)):
        #print(int(myString[i] ) * 2, end = "")
        newString = newString + str(int(myString[i]) * 2);

    #print("")

    for character in newString:
        sum_of_digits = sum_of_digits + int(character)


    #print(sum_of_digits)
    total_sum = total_sum + sum_of_digits


    #print("first sum ", sum_of_digits)
    #print("")

    for i in range(0, card_num_len, 2):
        #print(card_num_string[card_num_len - i - 1])

        total_sum = total_sum + int(card_num_string[card_num_len - i - 1])

    #print("total sum ", total_sum)
    #print("")


    if total_sum % 10 == 0:
        card_valid = True;

    else:
        card_valid = False;

    """
    American Express numbers start with 34 or 37;
    most MasterCard numbers start with 51, 52, 53, 54, or 55
    and all Visa numbers start with 4.
    """
    if card_valid == True:
        #print(card_num_string)

        if int(card_num_string[0]) == 4:
            print("VISA")

        elif int(card_num_string[0:2]) == 34 or int(card_num_string[0:2]) == 37:
            print("AMEX")

        elif int(card_num_string[0:2]) == 51 or int(card_num_string[0:2]) == 52 or int(card_num_string[0:2]) == 53 or int(card_num_string[0:2]) == 54 or int(card_num_string[0:2]) == 55:
            print("MASTERCARD")

    else:
        print("INVALID")

    return card_valid


