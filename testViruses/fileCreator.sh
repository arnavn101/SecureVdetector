for n in {1..10}; do
    dd if=/dev/urandom of=file$( printf %04d "$n" ).bin bs=10M count=1
    sleep 1
done