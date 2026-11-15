args <- commandArgs(trailingOnly = TRUE)
if (length(args) != 2) stop("Usage: Rscript plot.R input.csv output.png")
data <- read.csv(args[1])
if (!all(c("x", "y") %in% names(data))) stop("CSV needs x and y columns")
if (nrow(data) < 2 || !all(is.finite(data$x)) || !all(is.finite(data$y)) ||
    length(unique(data$x)) < 2) stop("Need complete finite observations and varying x")
model <- lm(y ~ x, data = data)
print(summary(model))
cat(sprintf("slope=%.17g\nintercept=%.17g\n", coef(model)[["x"]], coef(model)[["(Intercept)"]]))
dir.create(dirname(args[2]), showWarnings = FALSE, recursive = TRUE)
png(args[2], width = 1280, height = 720, pointsize = 22)
par(mar = c(4.2, 4.5, 2.8, 1.2), mgp = c(2.6, 0.8, 0), las = 1)
plot(data$x, data$y, xlab = "x", ylab = "y", pch = 19,
     col = adjustcolor("#5e33bf", alpha.f = 0.6), cex = 1.05,
     main = "Same CSV, R analysis")
abline(model, col = "black", lwd = 3)
dev.off()
