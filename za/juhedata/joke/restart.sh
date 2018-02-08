
i=1
while (( i<=4 )); do
    python main.py restart worker-${i} &
    (( i++ ))
done
wait

