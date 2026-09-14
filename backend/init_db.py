#!/usr/bin/env python
"""
Script to populate the database with initial problems for development.
Run this script directly using:
python3 manage.py shell < init_db.py
"""

from hints.models import Problem

# Delete existing problems to avoid duplicates
Problem.objects.all().delete()
print("Cleared existing problems")

# Create sample problems
problems = [
    {
        'problem_id': 'LC-1',
        'title': 'Two Sum',
        'description': """
Given an array of integers `nums` and an integer `target`, return indices of the two numbers such that they add up to `target`.

You may assume that each input would have exactly one solution, and you may not use the same element twice.

You can return the answer in any order.

Example 1:
Input: nums = [2,7,11,15], target = 9
Output: [0,1]
Explanation: Because nums[0] + nums[1] == 9, we return [0, 1].

Example 2:
Input: nums = [3,2,4], target = 6
Output: [1,2]

Example 3:
Input: nums = [3,3], target = 6
Output: [0,1]
        """,
        'difficulty': 'easy',
        'topic': 'Arrays'
    },
    {
        'problem_id': 'LC-2',
        'title': 'Add Two Numbers',
        'description': """
You are given two non-empty linked lists representing two non-negative integers. The digits are stored in reverse order, and each of their nodes contains a single digit. Add the two numbers and return the sum as a linked list.

You may assume the two numbers do not contain any leading zero, except the number 0 itself.

Example 1:
Input: l1 = [2,4,3], l2 = [5,6,4]
Output: [7,0,8]
Explanation: 342 + 465 = 807.

Example 2:
Input: l1 = [0], l2 = [0]
Output: [0]

Example 3:
Input: l1 = [9,9,9,9,9,9,9], l2 = [9,9,9,9]
Output: [8,9,9,9,0,1]
        """,
        'difficulty': 'medium',
        'topic': 'Linked List'
    },
    {
        'problem_id': 'LC-3',
        'title': 'Longest Substring Without Repeating Characters',
        'description': """
Given a string `s`, find the length of the longest substring without repeating characters.

Example 1:
Input: s = "abcabcbb"
Output: 3
Explanation: The answer is "abc", with the length of 3.

Example 2:
Input: s = "bbbbb"
Output: 1
Explanation: The answer is "b", with the length of 1.

Example 3:
Input: s = "pwwkew"
Output: 3
Explanation: The answer is "wke", with the length of 3.
Notice that the answer must be a substring, "pwke" is a subsequence and not a substring.
        """,
        'difficulty': 'medium',
        'topic': 'String'
    },
    {
        'problem_id': 'LC-4',
        'title': 'Median of Two Sorted Arrays',
        'description': """
Given two sorted arrays `nums1` and `nums2` of size `m` and `n` respectively, return the median of the two sorted arrays.

The overall run time complexity should be O(log (m+n)).

Example 1:
Input: nums1 = [1,3], nums2 = [2]
Output: 2.00000
Explanation: merged array = [1,2,3] and median is 2.

Example 2:
Input: nums1 = [1,2], nums2 = [3,4]
Output: 2.50000
Explanation: merged array = [1,2,3,4] and median is (2 + 3) / 2 = 2.5.
        """,
        'difficulty': 'hard',
        'topic': 'Array'
    },
    {
        'problem_id': 'LC-5',
        'title': 'Valid Parentheses',
        'description': """
Given a string `s` containing just the characters '(', ')', '{', '}', '[' and ']', determine if the input string is valid.

An input string is valid if:
1. Open brackets must be closed by the same type of brackets.
2. Open brackets must be closed in the correct order.
3. Every close bracket has a corresponding open bracket of the same type.

Example 1:
Input: s = "()"
Output: true

Example 2:
Input: s = "()[]{}"
Output: true

Example 3:
Input: s = "(]"
Output: false
        """,
        'difficulty': 'easy',
        'topic': 'Stack'
    },
    {
        'problem_id': 'LC-6',
        'title': 'Merge Two Sorted Lists',
        'description': """
You are given the heads of two sorted linked lists `list1` and `list2`.

Merge the two lists into one sorted list. The list should be made by splicing together the nodes of the first two lists.

Return the head of the merged linked list.

Example 1:
Input: list1 = [1,2,4], list2 = [1,3,4]
Output: [1,1,2,3,4,4]

Example 2:
Input: list1 = [], list2 = []
Output: []

Example 3:
Input: list1 = [], list2 = [0]
Output: [0]
        """,
        'difficulty': 'easy',
        'topic': 'Linked List'
    },
    {
        'problem_id': 'LC-7',
        'title': 'Binary Tree Level Order Traversal',
        'description': """
Given the `root` of a binary tree, return the level order traversal of its nodes' values. (i.e., from left to right, level by level).

Example 1:
Input: root = [3,9,20,null,null,15,7]
Output: [[3],[9,20],[15,7]]

Example 2:
Input: root = [1]
Output: [[1]]

Example 3:
Input: root = []
Output: []
        """,
        'difficulty': 'medium',
        'topic': 'Binary Tree'
    },
    {
        'problem_id': 'LC-8',
        'title': 'Maximum Depth of Binary Tree',
        'description': """
Given the `root` of a binary tree, return its maximum depth.

A binary tree's maximum depth is the number of nodes along the longest path from the root node down to the farthest leaf node.

Example 1:
Input: root = [3,9,20,null,null,15,7]
Output: 3

Example 2:
Input: root = [1,null,2]
Output: 2
        """,
        'difficulty': 'easy',
        'topic': 'Binary Tree'
    }
]

# Create the problems
for problem_data in problems:
    Problem.objects.create(**problem_data)
    print(f"Created problem: {problem_data['title']}")

print(f"\nSuccessfully created {len(problems)} problems")