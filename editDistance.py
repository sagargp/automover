def editDistance(s1, s2):
  from numpy import zeros 

  m = zeros([len(s1), len(s2)], int)
  m[0, 0] = 0

  for i in range(0, len(s1)):
    m[i, 0] = i

  for j in range(0, len(s2)):
    m[0, j] = j

  for i in range(1, len(s1)):
    for j in range(1, len(s2)):
      if s1[i-1] == s2[j-1]:
        m[i, j] = m[i-1, j-1]
      else:
        m[i, j] = 1 + min(m[i, j-1], m[i-1, j], m[i-1, j-1])

  return m[len(s1)-1, len(s2)-1]


if __name__ == '__main__':
  import sys
  print editDistance(sys.argv[1], sys.argv[2])
