
i=1
while (( i<=4 )); do
    python main.py stop worker-${i} &
    (( i++ ))
done
wait

