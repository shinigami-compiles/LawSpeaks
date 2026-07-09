/*
===========================================
NYAYAGPT – FRONTEND API HANDLER
===========================================

Purpose:
- Centralized API communication with FastAPI backend
- Handles all 7 endpoints
- Error handling + response formatting
- Easy reuse across all pages

Backend URL:
Change this if deployed
===========================================
*/

const BASE_URL = window.location.origin;

/* ----------------------------------------
   GENERIC POST REQUEST HANDLER
---------------------------------------- */
async function postRequest(endpoint, data) {

    showLoader(); // 🔥 start loader

    try {
        const response = await fetch(`${BASE_URL}${endpoint}`, {
            method: "POST",
            headers: {
                "Content-Type": "application/json"
            },
            body: JSON.stringify(data)
        });

        if (!response.ok) {
            throw new Error(`Server Error: ${response.status}`);
        }

        const result = await response.json();

        return result.response || "⚠️ No response received from server.";

    } catch (error) {
        console.error("API Error:", error);

        return "⚠️ Unable to connect to server. Please try again later.\n\nDisclaimer: This is general legal information.";

    } finally {
        hideLoader(); // 🔥 stop loader
    }

    console.log("API CALLED");
}

/* ----------------------------------------
   FEATURE 1: ASK LEGAL QUESTION
---------------------------------------- */
async function askQuestion(query) {
    return await postRequest("/ask", { query });
}

/* ----------------------------------------
   FEATURE 2: KNOW YOUR RIGHTS
---------------------------------------- */
async function getRights(category) {
    return await postRequest("/rights", { category });
}

/* ----------------------------------------
   FEATURE 3: LEGAL ACTION GUIDE
---------------------------------------- */
async function getActionGuide(action_type) {
    return await postRequest("/action-guide", { action_type });
}

/* ----------------------------------------
   FEATURE 4: CASE EXAMPLES
---------------------------------------- */
async function getCaseExamples(issue) {
    return await postRequest("/cases", { issue });
}

/* ----------------------------------------
   FEATURE 5: LAW LIBRARY
---------------------------------------- */
async function getLawLibrary(law_query) {
    return await postRequest("/library", { law_query });
}

/* ----------------------------------------
   FEATURE 6: MY LEGAL SITUATION
---------------------------------------- */
async function getSituation(situation_details) {
    return await postRequest("/situation", { situation_details });
}

/* ----------------------------------------
   FEATURE 7: RISK CHECKER
---------------------------------------- */
async function getRiskCheck(issue) {
    return await postRequest("/risk-check", { issue });
}

/* ----------------------------------------

/* ----------------------------------------
   RESPONSE RENDER UTILITY
---------------------------------------- */
function renderResponse(elementId, text) {
    const el = document.getElementById(elementId);
    if (el) {
        el.innerText = text;
    }
}

/* ----------------------------------------
   EXPORT (for global use)
---------------------------------------- */
window.NyayaAPI = {
    askQuestion,
    getRights,
    getActionGuide,
    getCaseExamples,
    getLawLibrary,
    getSituation,
    getRiskCheck,
    renderResponse
};