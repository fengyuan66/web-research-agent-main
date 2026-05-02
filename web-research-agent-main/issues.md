https://docs.google.com/document/d/1-lmq16x1NxEygHrhHOAU2-Xn7qNxGA4-PTF2xrq_Jgw/edit?usp=sharing

Here is link to a Google Doc containing logs and results of good / bad runs. The exact integrity of the runs you can see through the output.json given. These (at least at the time written, 2026-05-02, 12:32 AM), are all done after the Claude analysis intervention and the switch to Hack Club Search (Brave) instead of Serper.dev for API.

One issue that I want to point out right now is that the Llama API calling may not be very consistent, resulting in random results for every run. Overall the results are very satisfactory. However through the 1st run this is a problem that was noted:

"The Llama API is failing on the first attempt (returning empty output), then retrying and eventually succeeding—though the second attempt produces malformed empty queries before finally generating proper search results on the third try."

The API request for llama fails sometimes, but then sometimes it works. If the API fails in a crucial time and the pipeline does not give it a second round to get up, it could explain the previous issue where calling browsing tools fails randomly. Nonetheless it is relatively stable now (at least at this time, through some trials), so I'd say it is satisfactory.