// This is a temporary mock file to allow the frontend to build and run locally.
// This data will be replaced by the curated problems loaded from the backend API.
const problems = [
  {
    id: 1,
    problem_id: 'LC-1',
    title: 'Two Sum',
    topic: 'Arrays',
    difficulty: 'Easy',
    description: `Given an array of integers nums and an integer target, return indices of the two numbers such that they add up to target. You may assume that each input would have exactly one solution. You can return the answer in any order.`,
    starting_code: `function twoSum(nums, target) {\n  // write your code here\n}`,
    tests: [
      { input: '[2,7,11,15], 9', expected: '[0,1]' },
      { input: '[3,2,4], 6', expected: '[1,2]' }
    ]
  },
  {
    id: 2,
    problem_id: 'LC-2',
    title: 'Add Two Numbers',
    topic: 'Linked List',
    difficulty: 'Medium',
    description: `You are given two non-empty linked lists representing two non-negative integers. The digits are stored in reverse order and each of their nodes contains a single digit. Add the two numbers and return the sum as a linked list.`,
    starting_code: `// Linked list helper functions omitted for brevity\nfunction addTwoNumbers(l1, l2) {\n  // write your code here\n}`,
    tests: [
      { input: '[2,4,3], [5,6,4]', expected: '[7,0,8]' }
    ]
  }
]

export default problems
