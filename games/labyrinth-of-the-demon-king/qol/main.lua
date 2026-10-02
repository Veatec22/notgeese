-- Labyrinth of the Demon King QoL (local, ultrawide).
-- 1. In-engine cutscenes switch LocalPlayer.AspectRatioAxisConstraint to MaintainXFOV
--    and never restore it (gameplay stays zoomed in until a restart): keep MaintainYFOV.
-- 2. Cutscene cine cameras constrain to their filmback aspect (~1.32, side bars).
--    Unconstrained + MaintainYFOV makes the FOV value vertical, so the sensor width is
--    set to the sensor height: the lens FOV becomes the original vertical FOV and the
--    framing keeps its height while the sides open up.
-- 3. UI_CinematicBlackBars draws letterbox bars (top/bottom) and the cutscene subtitles:
--    hide only the bar images, never the widget.
local TAG = "[notgeeseQoL] "
local FIX_AXIS, OPEN_CINE_CAMERAS, HIDE_LETTERBOX = true, true, true
local MAINTAIN_Y_FOV, HIDDEN = 0, 2
local done = {}

local function log(m) print(TAG .. tostring(m) .. "\n") end
local function valid(o) return o ~= nil and o:IsValid() end
local function once(key, message)
    if not done[key] then done[key] = true; log(message) end
end
local function name(o)
    local ok, s = pcall(function() return o:GetFName():ToString() end)
    return ok and s or "?"
end

local function fix_axis()
    local lp = FindFirstOf("LocalPlayer")
    if valid(lp) and lp.AspectRatioAxisConstraint ~= MAINTAIN_Y_FOV then
        lp.AspectRatioAxisConstraint = MAINTAIN_Y_FOV
        log("axis constraint reset to MaintainYFOV")
    end
end

local function open_cine_cameras()
    for _, cam in ipairs(FindAllOf("CineCameraComponent") or {}) do
        if valid(cam) and cam.bConstrainAspectRatio then
            local fb = cam.Filmback
            local w, h = fb.SensorWidth, fb.SensorHeight
            fb.SensorWidth = h
            cam.bConstrainAspectRatio = false
            log(string.format("cine camera %s opened (sensor %.2fx%.2f -> %.2fx%.2f)",
                name(cam:GetOuter()), w, h, cam.Filmback.SensorWidth, cam.Filmback.SensorHeight))
        end
    end
end

local function hide_letterbox()
    local bars = FindAllOf("UI_CinematicBlackBars_C") or {}
    if #bars == 0 then return end
    for _, img in ipairs(FindAllOf("Image") or {}) do
        if valid(img) then
            local ok, res = pcall(function() return img.Brush.ResourceObject end)
            if ok and valid(res) and name(res) == "BlackBars" and img:GetVisibility() ~= HIDDEN then
                img:SetVisibility(HIDDEN)
                once("bars" .. img:GetAddress(), "letterbox image hidden: " .. name(img))
            end
        end
    end
end

log("loaded")
LoopAsync(100, function()
    ExecuteInGameThread(function()
        if FIX_AXIS then local ok, e = pcall(fix_axis); if not ok then once("e1", "axis failed: " .. tostring(e)) end end
        if OPEN_CINE_CAMERAS then local ok, e = pcall(open_cine_cameras); if not ok then once("e2", "cine failed: " .. tostring(e)) end end
        if HIDE_LETTERBOX then local ok, e = pcall(hide_letterbox); if not ok then once("e3", "bars failed: " .. tostring(e)) end end
    end)
    return false
end)
