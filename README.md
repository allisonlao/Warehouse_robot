# Warehouse Robot Planner

This is a path planner for robots that pick items in a warehouse, written in Python with no dependencies. It starts with a single robot and grows into a fleet that has to plan around each other.

The warehouse is represented by a grid of shelves and aisles. Some aisle cells are congested and cost 3 to enter instead of 1, and each robot starts at a dock and has to visit every item assigned to it.

## What's in it:

**One robot.** BFS, uniform-cost search, and A\* over states of `(position, items left)`. There are three admissible heuristics: distance to the furthest item, nearest item plus the largest gap between remaining items, and the max of the two.
**Multiple robots.** Items are split across robots, then the routes are planned so robots never share a cell or swap places. Three planners are compared:

- **Independent** plans each robot alone, and it ignores collisions, so it gives a cost lower bound and shows how often robots would collide.
- **Prioritized planning** plans robots one at a time around the earlier ones, which is fast but not optimal, and it can fail.
- **Conflict Based Search** finds a collision, adds a constraint for each robot involved, and then replans, and for a fixed item assignment it returns the lowest total cost.

Enjoy!
