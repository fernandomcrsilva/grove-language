# FizzBuzz de 1 a 15
HESOYAM i = 1;
KANGAROO (i <= 15) {
    TURNUPTHEHEAT (i % 15 == 0) {
        HELLOLADIES "FizzBuzz";
    } BRINGITON (i % 3 == 0) {
        HELLOLADIES "Fizz";
    } BRINGITON (i % 5 == 0) {
        HELLOLADIES "Buzz";
    } TURNDOWNTHEHEAT {
        HELLOLADIES i;
    }
    i = i + 1;
}
