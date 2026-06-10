import os, glob, time
d = r'C:\omnet-workspace\flora\simulations\results'
groups = [('median-only',10),('abstain-only',10),('adaptive-step-attack',5),('adaptive-step-defense',5),('adaptive-random-attack',5),('adaptive-random-defense',5),('gw4-K1-attack',10),('gw4-K1-defense',10),('gw5-K2-attack',10),('gw5-K2-defense',10),('gw5-K3-attack',10),('gw5-K3-defense',10)]
total_expected = sum(e for _,e in groups)
total_done = 0
for g, expected in groups:
    files = glob.glob(os.path.join(d, '*'+g+'*.sca'))
    done = sum(1 for f in files if os.path.getsize(f) > 1000000)
    total_done += done
    st = 'DONE' if done==expected else ('RUNNING' if done>0 else 'waiting')
    print('{:30s} {:2d}/{:2d}  {}'.format(g, done, expected, st))
pct = 100*total_done//total_expected
print('Overall: {}/{} ({}%) @ {}'.format(total_done, total_expected, pct, time.strftime('%H:%M:%S')))
