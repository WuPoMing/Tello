clc;close all

filename = 'data.csv';
data = readmatrix(filename);
area = data(:, 2);
speed = data(:, 3);

subplot(2, 1, 1)
plot(area)
grid on
title('Input')
xlabel('Time(Seconds)')
ylabel('Face Area')

subplot(2, 1, 2)
plot(speed)
grid on
title('Output')
xlabel('Time(Seconds)')
ylabel('Speed')

plot(ss7)