% Code-reading example only: this course does not require executing MATLAB.
% Run from reference/ only if a licensed MATLAB environment is available.
data = readtable("data/base-001.csv");
coefficients = polyfit(data.x, data.y, 1);
slope = coefficients(1);
intercept = coefficients(2);
disp(coefficients); % Ask the Agent to replace this with named coefficient output.
fitted = intercept + slope .* data.x;
scatter(data.x, data.y);
hold on;
plot(data.x, fitted);
hold off;
xlabel("x"); ylabel("y");
legend("observations", "OLS fit");
