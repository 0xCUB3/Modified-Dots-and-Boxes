## n spokes, at least 5 vertices on each spoke, 1 loop
| Number of Spokes | Number of Loops | Sequence of Extra Vertices on Each Spoke | Winner | Score |
| -------- | ------- | ------- | ------- | ------- |
| 1 | 1 | 5 | P1 | (7 - 0) |
| 2 | 1 | 5,5 | P2 | (0 - 13) |
| 3 | 1 | 5,5,5 | P2 | (2 - 15) |
| 4 | 1 | 5,5,5,5 | P2 | (4 - 21) |
* Any greater number of spokes is too complex for the current algorithm
This pattern interestingly continues for any sequence of numbers where each is greater than or equal to 5.

## n spokes, at least 5 vertices on each spoke except one, 1 loop
| Number of Spokes | Number of Loops | Sequence of Extra Vertices on Each Spoke | Winner | Score |
| -------- | ------- | ------- | ------- | ------- |
| 2 | 1 | 5,2 | P2 | (0 - 10) |
| 3 | 1 | 5,5,2 | P2 | (2 - 14) |
| 4 | 1 | 5,5,5,2 | P2 | (4 - 18) |

I selected 2 for the remaining vertex because that is the largest number where there are fewer than 5 vertices in the spoke including the center vertex (2 extra + outer + center). 
