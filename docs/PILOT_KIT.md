# TasteProbe voluntary pilot kit

## Invitation — draft for Nourhan to share
I am testing TasteProbe, an experimental movie-discovery app built with Qloo.
Would you volunteer for a short comparison of two question approaches? Please
participate only if you are 18 or older. You will choose favorite films, answer up
to six questions, and rate familiar suggestions. No account or contact details are
needed in the app. Participation is optional, and you can stop without sharing data.

Try https://tasteprobe.onrender.com/ and select Live Qloo, then “Compare two
approaches.” Read the consent statement before deciding whether to proceed. The
free server may need time to wake, and live rankings can take around a minute.
If you voluntarily share your exported JSON with me, I will use the anonymous taste
answers and ratings to summarize this exploratory hackathon pilot. Do not include
personal information. Review the export before sharing; it includes your favorites.

Before sending this invitation, the organizer should specify an agreed return
channel and deletion date. The agent has not contacted anyone or enrolled participants.

## Participant steps
1. Search and confirm two favorite movies you know. Avoid sharing sensitive information.
2. Enable the comparison, read the statement, and consent only if you choose to.
3. Complete the two rounds honestly; use Unfamiliar when unsure. Questions may repeat.
4. Rate only familiar final films for stated taste fit, not imagined viewing outcomes.
5. Export only if you want to share. Review the JSON; do not add a name or email.
6. Return it through the organizer's agreed private channel. Participate once.

## Organizer handling
Aim for 10–20 exploratory participants, without treating that target as statistical
power. Keep exports out of the public GitHub repository. Explain the actual retention
period before collection and honor withdrawal requests while files remain identifiable.
Assign random file labels; keep any contact-to-file mapping separately and only with
permission. Do not record nonparticipants as failures or substitute generated ratings.

Run `python analyze_paired.py path/to/export1.json path/to/export2.json`.
Keep all exclusions and denominators. Report live-source sessions separately from
synthetic trials. Summaries are descriptive; do not claim significance or causal uplift.

## Results template — currently no participant data
Invited: not recorded. Completed live paired sessions: 0 collected by this agent.
Eligible sessions with ratings in both arms: not yet available.
Adaptive-minus-fixed mean stated-fit rating: not yet available.
Rating coverage, question count, skip count, missingness: not yet available.
Recruitment limitations and order/carryover effects: report with actual results.
