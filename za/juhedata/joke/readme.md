

### v0.0.1 2015.12.19 bourneair

getText?page=%d
getImg?page=%d

####

i=1
while (( i<=4 )); do
    python main.py restart joke${i} &
    (( i++ ))
done
wait

