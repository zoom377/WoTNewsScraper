
import math


def is_palindrome(x: int) -> bool:

    x_str = str(x)
    # print(f"{x_str} : {len(x_str)}")

    print(x_str)

    x_str_rev = ""
    for c in reversed(x_str):
        x_str_rev += c

    print(x_str_rev)

    return False


# Definition for singly-linked list.
class ListNode(object):
    def __init__(self, val=0, next=None):
        self.val = val
        self.next = next

    def __str__(self) -> str:
        return_str = str(self.val)
        current = self

        while current.next is not None:
            current = current.next
            return_str += f" -> {current.val}"

        return return_str


def linked_list_to_int(list_node) -> int:
    i = 1
    number: int = 0 + list_node.val

    while True:
        list_node = list_node.next
        if list_node is None:
            break
        number += list_node.val * math.pow(10, i)
        i += 1

    return number


def int_to_linked_list(number: int) -> int:
    first_node = ListNode(number % 10)
    cur_node = first_node

    while True:
        number = number // 10
        if number == 0:
            break

        next_node = ListNode()
        next_node.val = number % 10
        cur_node.next = next_node
        cur_node = next_node

    return first_node


def addTwoNumbers(self, l1, l2):
    """
    :type l1: ListNode
    :type l2: ListNode
    :rtype: ListNode
    """
    num1 = linked_list_to_int(l1)
    num2 = linked_list_to_int(l2)
    return int_to_linked_list(num1 + num2)


link1 = ListNode(1)
link2 = ListNode(2)
link3 = ListNode(3)
link1.next = link2
link2.next = link3

print(link1)
number = linked_list_to_int(link1)
print(number)
print(int_to_linked_list(number))
