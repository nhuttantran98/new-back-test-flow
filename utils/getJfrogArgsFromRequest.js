function getJfrogArgsFromRequest(req, res) {
    const args = [];
    const { "jfrog-url": jfrogUrl, "jfrog-repo": jfrogRepo, "jfrog-token": jfrogToken } = req.body;
    if (!jfrogUrl || !jfrogRepo || !jfrogToken) {
        return res.status(400).json({
            success: false,
            message: "Missing required JFrog parameters"
        });
    }
    args.push(jfrogUrl);
    args.push(jfrogRepo);
    args.push(jfrogToken);
    return args;
}

module.exports = { getJfrogArgsFromRequest };