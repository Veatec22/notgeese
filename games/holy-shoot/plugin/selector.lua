-- Pure adapter: retain every existing entry and append one culture.
local M = {}

function M.plan(labels, codes)
    assert(#labels > 0, "Language options are not initialized yet")
    local polish
    for i, label in ipairs(labels) do
        local code = codes[i - 1]
        assert(type(code) == "string" and code ~= "", "Language map and options differ")
        if code == "pl" then
            assert(not polish, "Duplicate Polish culture")
            polish = i - 1
        elseif label == "Polski" then
            error("Polish label belongs to another culture")
        end
    end
    if polish then return labels, polish, false end
    assert(codes[#labels] == nil, "Next language index already occupied")
    assert(#labels < 255, "Language byte index exhausted")
    local result = {}
    for i, label in ipairs(labels) do result[i] = label end
    result[#result + 1] = "Polski"
    return result, #labels, true
end

return M
