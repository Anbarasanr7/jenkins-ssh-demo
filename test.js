console.log("Running test...");

if (process.env.FAIL_TEST === "true") {
    console.error("Test Failed!");
    process.exit(1);
}

console.log("Test Passed!");
