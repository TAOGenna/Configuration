---
name: hunting-big-bets
description: Use when looking for the highest-impact thing to build or pitch at a company — "what should we build next", "biggest lever", "what would move the needle", "find me a big idea", joining a new team or codebase, or picking what to prototype instead of working the backlog.
---

# Hunting big bets

A **bet** is one idea that, if it works, moves the company's top goal a lot, and that you can show working before anyone has to believe you. Execution is cheap now, so status isn't the gate anymore. A working prototype of a good bet is. Hunger beats tenure.

The output is **one bet, built, and pitched**. Not a list of ideas.

## Steps

0. **Load the world model.** Read `~/.claude/hunting-big-bets/worlds/<company>.md`. World models stay in that local folder, outside this skill, because they hold private company data and this skill may be installed from a public repo. It is a map of the product, the tech, the money, the goals and the pulse, and every claim in it carries a date and a source. Re-verify any number your bet depends on, because the map ages. If no world model exists for the company, build one with the same sections before step 1. When you finish, write back what you verified or corrected, with today's date.
   *Done when* you know which of the world model's facts your hunt relies on, and which of those you still have to check.

1. **Find the goal at altitude.** Work out what the company is actually trying to do, and what your manager's manager is measured on. Follow the money: who pays, for what, and why they stop paying. Money is the map, not the territory. The territory is the value a real user gets, so name that value too.
   *Done when* you can write one sentence for the goal, the number that tracks it, and that number's current value, taken from real data rather than a deck. If you can't read the number, stop and get access to it. Every later step ranks bets by their effect on this number, so working from a proxy turns the whole hunt into a guess. If there are several goals and none has an owner, pick the one the people funding the company would name first. If you can't tell which that is, finding out is your first question.

2. **Walk the territory with fresh eyes.** Use the product the way a paying user does, start to finish, and write down every odd, slow or broken moment. Then list what "everyone knows" is impossible or not worth it, and check at least one of those beliefs against raw data or code. Most of them were never checked.
   *Done when* you have friction notes from your own use of the product, plus at least one "impossible" belief that you checked and found wrong, or confirmed.

3. **Measure the distance to the leader.** Pick the one competitor that actually matters. Compare yourself axis by axis (users, data, compute, spend, speed, price) and write each gap in orders of magnitude. Mark the gaps you could close cheaply. comma closed inference compute from 100x to 1x with a $300 consumer GPU. Extend the trend lines to estimate when things land: every order of magnitude takes about the same time.
   *Done when* you have a table of axes, gaps and cheap closers. A rough table built from public numbers counts; skipping the table does not.

4. **Generate 3–5 radical candidates.** Each one, if it works, moves the step-1 number a lot, not by a few percent. Good sources are the step-2 friction, the step-3 cheap closers, and the goal beyond the goal (fixing crashes becomes keeping the app crash-free). Ask a different question from the leader: Tesla asks "what crazy feature can we ship?", comma asks "how do we reach highway perfection?".
   *Done when* each candidate states its mechanism: "X changes, so the user does Y, so the number moves by roughly Z."

5. **Run every candidate through Outwit, Outplay and Outlast below, and keep one.** The survivor is the candidate with the biggest effect on the number among those that pass all three. Do not hide three good ideas among twenty bad ones in one prototype.
   *Done when* exactly one bet remains and you can say in one line why each of the others died.

6. **Build it over a weekend.** It must be a working prototype on real data, scoped to that one idea, with an outside judge that shows it works: a metric, a replay or a test, never your own opinion. Set an unreasonable target, such as 200 ms instead of 5 s, and keep going. Don't ask to be "put to work": bring the work already done.
   *Done when* someone can run it and watch the step-1 number, or a credible proxy for it, move. If you can't build it in this session, write it as a runnable experiment instead: the data, the split, the judge and the target. Then stop, and don't pitch until it has run.

7. **Pitch it to someone who can say yes.** A committee can only say no, so find the one person who owns the goal. The pitch is short, in this order: the goal and its number; the bet; what the consensus believes that is wrong; the demo; what the bet costs to keep alive; what you need.
   *Done when* the pitch fits on one screen and opens with the demo link.

## Outwit, Outplay, Outlast (step 5)

Kill the candidate if any line below is true. A candidate dies on the first true line, so you don't need to check the rest for an obvious loser.

**Outwit: be right where the consensus is wrong**
- **No wrong consensus:** it doesn't name what the incumbents or the team believe that you think is false (comma: LIDAR, HD maps, hand-coded rules). If everyone already agrees, there is no edge.
- **Wrong game:** competitors would win by doing the same thing with more money.
- **No Mr. Ford:** adoption depends on a partner, buyer or org where nobody can say yes. Selling to carmakers was fake legitimacy; comma sold directly to drivers.
- **Builds the car:** it rebuilds the commodity around the core capability. "A self-driving car is not a car; it's a dude." Build the self-driving.
- **Cone guy:** it hard-codes rules, word lists or special cases where a general method, search or learning on real data, would scale.
- **Fails the six-year-old test:** you can't explain it to a six-year-old, or a user can't actually get it and use it today. A video, a roadmap or a press release is not technology.

**Outplay: execute better and cheaper**
- **Extra parts:** it adds a layer whose job is to work around another layer. The best part is no part, so prefer the bet that deletes code, steps or config.
- **Chip before software:** it does the visible, flashy part and leaves the hard, unglamorous part that makes it usable.
- **Undifferentiated at its price:** it's better but not different enough for what it costs. comma 3 was a big improvement, sales stagnated, and it lost $5M; the cheaper 3X fixed sales. Price it to how much it gets used: a $1,000 device used on 40% of days is worth it, a robot toy is worth $200.
- **Bigger form than needed:** a simpler form delivers about 95% of the value. Home security needs a fixed camera, a speaker and good software, not a robot.
- **Options over polish:** it needs many configurations or a confusing name. One configuration, tested end to end on every unit, beats ten variants; when you improve it, the number goes up by one.
- **Extracts value:** dark patterns, lock-in, revocable access, complexity it pushes onto users, rent-seeking. Never let a plateau turn into "let's exploit: raise the subscription, add ads". Test: would you still build it if the money went away?

**Outlast: survival is the win condition in an infinite game**
- **Can't pay its way:** it needs a big raise or a long burn before it shows value. Cruise spent $10B and Argo $2.7B before dying; comma is profitable.
- **Buys speed with risk:** "How much extra risk will you take to close the gap? Zero." Being two years behind the leader is fine if the business sustains itself.
- **Moonshot without profit behind it:** a profitable company can spend 0.1% of its budget on a moonshot. A bet that only makes sense when funded by hope is dead.
- **Narrative timeline:** its timing rests on hype ("next week") or doom ("never") instead of a measured trend line extended forward.

## Your edge

- **New or junior:** your naïveté is the asset. Ask the "obvious" question, and notice the friction the veterans stopped seeing. Your handicap is that nobody listens to you, which is why step 6 comes before step 7.
- **User-facing work:** you still feel what an outsider feels. Use that before it fades.
- **Infra or tooling:** you never learned why things are "impossible". Check whether they are.
- **Expect it to be harder than it looks.** You start because you think it's easy; plan to survive it being hard (comma took four years to go from comma one to comma two). Ignore media and outside narratives about your bet: "when they go left, eat a cheesecake".

## Common mistakes

- Returning a ranked list of ideas instead of one bet.
- Picking from the backlog. The backlog is the consensus.
- Writing a PRD or design doc instead of a prototype.
- Letting the model judge its own result instead of using an outside check.
- Role-playing experts ("act like a short seller") instead of doing what they do (pulling the raw numbers).

Sources and the full distillation: [sources.md](sources.md).
