from subprocess import run


command = ['blastp', '-query', 'PT_tree_primary', '-db', '../static/genome/pep/carrot', '-outfmt', '6', '-evalue', '0.001']
print(command)
blast_process = run(command, capture_output=True)
print(blast_process)
print('1')
blast_result = blast_process.stdout.decode('utf-8')
print(blast_result)
print('2')
