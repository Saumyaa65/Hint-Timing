import json
import os
import re
from collections import Counter

def curate_problems(input_file, output_file, target_total=1400):
    print(f"Starting Intelligent Curation...")
    
    # Master Roadmap from User
    roadmap = {
        'Arrays & Hashing': ['Two Sum', 'Valid Anagram', 'Contains Duplicate', 'Group Anagrams', 'Top K Frequent Elements', 'Product of Array Except Self', 'Valid Sudoku', 'Longest Consecutive Sequence', 'Encode and Decode Strings', 'Majority Element'],
        'Two Pointers': ['Valid Palindrome', '3Sum', 'Container With Most Water', 'Trapping Rain Water', 'Two Sum II', 'Sort Colors', 'Move Zeroes', 'Remove Duplicates from Sorted Array', 'Boats to Save People', '4Sum'],
        'Binary Search': ['Binary Search', 'Search in Rotated Array', 'Minimum in Rotated Array', 'Koko Eating Bananas', 'Median of Two Arrays', 'Search a 2D Matrix', 'Time Based Key-Value Store', 'Capacity to Ship Packages Within D Days', 'Find First and Last Position of Element in Sorted Array', 'Find Peak Element'],
        'Stacks': ['Valid Parentheses', 'Min Stack', 'Daily Temperatures', 'Generate Parentheses', 'Largest Rectangle in Histogram', 'Evaluate Reverse Polish Notation', 'Car Fleet', 'Asteroid Collision', 'Remove K Digits', 'Next Greater Element I'],
        'Sliding Window': ['Best Time to Buy and Sell Stock', 'Substring Without Repetition', 'Minimum Window Substring', 'Character Replacement', 'Sliding Window Maximum', 'Permutation in String', 'Fruits into Baskets', 'Minimum Size Subarray Sum', 'Subarray Product Less Than K', 'Max Consecutive Ones III'],
        'Linked List': ['Reverse Linked List', 'Merge Two Sorted Lists', 'Linked List Cycle', 'Reorder List', 'Merge K Sorted Lists', 'Remove Nth Node From End of List', 'Copy List With Random Pointer', 'Add Two Numbers', 'LRU Cache', 'Reverse Nodes in K-Group'],
        'Trees': ['Binary Tree Level Order', 'Maximum Depth of Binary Tree', 'Lowest Common Ancestor', 'Binary Tree Maximum Path Sum', 'Serialize and Deserialize', 'Invert Binary Tree', 'Diameter of Binary Tree', 'Validate Binary Search Tree', 'Binary Tree Right Side View', 'Construct Binary Tree from Preorder and Inorder Traversal'],
        'Heap / Priority Queue': ['Kth Largest Element in an Array', 'K Closest Points to Origin', 'Task Scheduler', 'Find Median from Data Stream', 'Merge K Sorted Lists', 'Kth Largest Element in a Stream', 'Last Stone Weight', 'Design Twitter', 'Reorganize String', 'Sliding Window Median'],
        'Backtracking': ['Subsets', 'Combination Sum', 'Permutations', 'Word Search', 'N-Queens', 'Subsets II', 'Combination Sum II', 'Palindrome Partitioning', 'Letter Combinations of a Phone Number', 'Sudoku Solver'],
        'Tries': ['Implement Trie', 'Design Add and Search Words', 'Word Search II', 'Longest Common Prefix', 'Replace Words', 'Extra Characters in a String', 'Sum of Prefix Scores of Strings', 'Palindrome Pairs', 'Index Pairs of a String', 'Search Suggestions System'],
        'Graphs': ['Number of Islands', 'Clone Graph', 'Pacific Atlantic Water Flow', 'Course Schedule', 'Word Ladder', 'Max Area of Island', 'Rotting Oranges', 'Course Schedule II', 'Redundant Connection', 'Number of Connected Components in an Undirected Graph'],
        'Advanced Graphs': ['Network Delay Time', 'Min Cost to Connect All Points', 'Cheapest Flights Within K Stops', 'Swim in Rising Water', 'Reconstruct Itinerary', 'Alien Dictionary', 'Path with Maximum Probability', 'Find the City With the Smallest Number of Neighbors at a Threshold Distance', 'Minimum Spanning Tree', 'Shortest Path in Binary Matrix'],
        '1-D Dynamic Programming': ['Climbing Stairs', 'House Robber', 'Coin Change', 'Longest Increasing Subsequence', 'Word Break', 'House Robber II', 'Decode Ways', 'Longest Palindromic Substring', 'Partition Equal Subset Sum', 'Maximum Product Subarray'],
        '2-D Dynamic Programming': ['Unique Paths', 'Longest Common Subsequence', 'Edit Distance', 'Burst Balloons', 'Regular Expression Matching', 'Best Time to Buy and Sell Stock with Cooldown', 'Coin Change II', 'Target Sum', 'Interleaving String', 'Distinct Subsequences'],
        'Greedy': ['Jump Game', 'Jump Game II', 'Gas Station', 'Partition Labels', 'Non-overlapping Intervals', 'Hand of Straights', 'Merge Triplets to Form Target Triplet', 'Valid Parenthesis String', 'Candy', 'IPO'],
        'Intervals': ['Merge Intervals', 'Insert Interval', 'Non-overlapping Intervals', 'Meeting Rooms', 'Min. Interval to Include Query', 'Meeting Rooms II', 'Employee Free Time', 'Car Pooling', 'Interval List Intersections', 'My Calendar I'],
        'Bit Manipulation': ['Single Number', 'Number of 1 Bits', 'Counting Bits', 'Reverse Bits', 'Sum of Two Integers', 'Missing Number', 'Reverse Integer', 'Power of Two', 'Bitwise AND of Numbers Range', 'Single Number II'],
        'Math & Geometry': ['Rotate Image', 'Spiral Matrix', 'Set Matrix Zeroes', 'Happy Number', 'Pow(x, n)', 'Multiply Strings', 'Detect Squares', 'Plus One', 'Count Primes', 'Excel Sheet Column Number']
    }

    # Map raw data labels to Roadmap categories
    category_map = {
        'array': 'Arrays & Hashing',
        'string': 'Sliding Window',
        'dp': '1-D Dynamic Programming',
        'dynamic programming': '1-D Dynamic Programming',
        'tree': 'Trees',
        'graph': 'Graphs',
        'linked list': 'Linked List',
        'stack': 'Stacks',
        'heap': 'Heap / Priority Queue',
        'backtracking': 'Backtracking',
        'trie': 'Tries',
        'math': 'Math & Geometry',
        'bit': 'Bit Manipulation',
        'interval': 'Intervals'
    }

    all_priority_titles = [title.lower() for titles in roadmap.values() for title in titles]
    topic_quotas = {k: 80 for k in roadmap.keys()}

    curated_count = 0
    topic_counts = Counter()
    seen_titles = set()
    
    with open(input_file, 'r', encoding='utf-8') as f_in, \
         open(output_file, 'w', encoding='utf-8') as f_out:
        
        for line in f_in:
            try:
                problem = json.loads(line)
                title = problem.get('title', '').strip()
                explanation = problem.get('problem_explanation', '')
                
                if not title or len(explanation) < 50:
                    continue
                
                normalized_title = re.sub(r'[^a-zA-Z0-9]', '', title.lower())
                if normalized_title in seen_titles:
                    continue

                # Smarter Categorization
                raw_cat = problem.get('category', '').lower()
                matched_topic = 'Other'
                
                # First check title for keywords
                for kw, roadmap_cat in category_map.items():
                    if kw in title.lower() or kw in raw_cat:
                        matched_topic = roadmap_cat
                        break

                is_vip = any(pattern in title.lower() for pattern in all_priority_titles)
                
                should_take = False
                if is_vip:
                    should_take = True
                elif topic_counts[matched_topic] < topic_quotas.get(matched_topic, 40):
                    should_take = True

                if should_take:
                    # Update the problem object with the better category
                    problem['roadmap_category'] = matched_topic
                    f_out.write(json.dumps(problem) + '\n')
                    seen_titles.add(normalized_title)
                    topic_counts[matched_topic] += 1
                    curated_count += 1
                    
                    if curated_count % 100 == 0:
                        print(f"Curated {curated_count} problems...")

                if curated_count >= target_total:
                    break

            except Exception:
                continue

    print(f"\nCuration Complete!")
    print(f"Total Curated: {curated_count}")
    print("\nTopic Distribution:")
    for topic, count in sorted(topic_counts.items(), key=lambda x: x[1], reverse=True):
        print(f" - {topic}: {count}")

if __name__ == "__main__":
    curate_problems("backend/problems_full.jsonl", "backend/curated_problems_1k.jsonl")
