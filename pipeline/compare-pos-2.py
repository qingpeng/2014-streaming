#! /usr/bin/env python
import argparse
import sys
import screed

# read in list of error positions per read

def read_pos_file(filename):
    for line in open(filename):
        line = line.strip()
        try:
            read, posns = line.split(' ', 2)
            posns = map(int, posns.split(','))
        except ValueError:
            read = line
            posns = []
            
        yield read, posns

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('ident')
    parser.add_argument('pos_a')
    parser.add_argument('pos_b')
    parser.add_argument('reads')
    args = parser.parse_args()

    # read in two lists of positions & errors
    a = dict(read_pos_file(args.pos_a))
    b = dict(read_pos_file(args.pos_b))

    # get list of all reads
    print >>sys.stderr, 'loading reads from', args.reads
    all_names = set()
    all_lengths = {}
    for record in screed.open(args.reads):
        all_names.add(record.name)
        all_lengths[record.name] = len(record.sequence)

    n = 0                               # in a
    m = 0                               # number of matches
    unexplained = 0
    
    for k, va in a.iteritems():
        if not va:
            continue
        
        n += 1
        vb = b.get(k)
        if not vb:
            continue
        
        if va == vb:                # match
            m += 1
        else:
            READLEN = all_lengths[k]
            rva = list(sorted([ READLEN - x - 1 for x in va ]))
            if rva == vb:           # match (reverse complement)
                m += 1
            else:
#                    print k, va, rva, vb # not a match
                unexplained += 1

    o = 0                               # in b
    for k, vb in b.iteritems():
        if len(vb):
            o += 1

#    print 'total # of reads analyzed: %d' % (len(a),)
#    print '%d erroneous reads in %s' % (n, args.pos_a)
#    print '%d erroneous reads in %s' % (o, args.pos_b)
#    print '%d reads in common => all error positions AGREE' % (m,)
#    print '%d DISAGREE' % (unexplained,)
#    print 'total # of reads:', len(all_names)

    # assume a is prediction, b is correct
    
    incorrect_in_a = set([ k for k in a if a[k] ])
    incorrect_in_b = set([ k for k in b if b[k] ])
    correct_in_a = all_names - set([ k for k in a if a[k] ])
    correct_in_b = all_names - set([ k for k in b if b[k] ])
    
    # m is reads thought to be erroneous by a, agree with b
    tp = m

    # fp: reads thought to be erroneous by a, but not in b
    #     + places where a called errors that were incorrect
    fp = len(incorrect_in_a.intersection(correct_in_b)) + unexplained

    # fn: reads through to be correct by a, but actually erroneous (in b)
    correct_in_a = all_names - incorrect_in_a
    fn = len(correct_in_a.intersection(incorrect_in_b))

    # tn: reads thought to be correct in both a and b
    tn = len(correct_in_a.intersection(correct_in_b))

    if tp + fp != 0:
        specificity = tp / float(tp + fp)
    else:
        specificity = -1

    if tp + fn != 0:
        sensitivity = tp / float(tp + fn)
    else:
        sensitivity = -1

    print args.ident, tp, tn, fp, unexplained, fp-unexplained, \
          sensitivity, specificity

    assert len(all_names) == tp+tn+fp+fn, len(all_names) - (tp+tn+fp+fn)
    
if __name__ == '__main__':
    main()
