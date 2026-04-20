const BIRDS = ['丹顶鹤', '朱鹮', '中华秋沙鸭', '勺嘴鹬', '黑脸琵鹭']

const LOCATIONS = [
  '俄罗斯远东',
  '中国东北',
  '朝鲜半岛',
  '日本北海道',
  '陕西洋县',
  '日本佐渡岛',
  '韩国重引入区',
  '俄罗斯楚科奇海岸',
  '黄海滩涂',
  '香港米埔湿地',
  '台湾台江湿地'
]

const HABITATS = ['湿地', '沼泽', '滩涂', '河谷稻田', '山地森林', '海岸苔原', '潮间带泥滩', '海岸湿地', '河口']
const STATUSES = ['CR', 'EN', 'VU', 'NT']
const THREATS = ['湿地丧失', '火灾', '气候变化', '栖息地破坏', '农药污染', '滩涂围垦', '猎捕压力', '水体污染']

function splitSentences(text) {
  return text
    .split(/[。！？]/)
    .map((sentence) => sentence.trim())
    .filter(Boolean)
}

function findFirst(list, sentence) {
  return list.find((item) => sentence.includes(item))
}

function findAll(list, sentence) {
  const matches = list
    .filter((item) => sentence.includes(item))
    .sort((left, right) => right.length - left.length)

  return matches.filter((candidate, index) => {
    return !matches.some((other, otherIndex) => {
      return otherIndex < index && other.includes(candidate)
    })
  })
}

function makeTriple(subject, predicate, object, objectType, evidence) {
  return {
    subject,
    predicate,
    object,
    subject_type: 'Bird',
    object_type: objectType,
    evidence
  }
}

function uniqueTriples(triples) {
  const cache = new Set()
  return triples.filter((triple) => {
    const key = JSON.stringify(triple)
    if (cache.has(key)) {
      return false
    }

    cache.add(key)
    return true
  })
}

export function extractTriplesFromText(text) {
  const triples = []

  for (const sentence of splitSentences(text)) {
    const subject = findFirst(BIRDS, sentence)
    if (!subject) {
      continue
    }

    if (/(分布于|分布在|繁殖于|越冬于|集中在)/.test(sentence)) {
      findAll(LOCATIONS, sentence).forEach((location) => {
        triples.push(makeTriple(subject, 'distributed_in', location, 'Location', sentence))
      })
    }

    if (/(栖息在|栖息于|依赖)/.test(sentence)) {
      findAll(HABITATS, sentence).forEach((habitat) => {
        triples.push(makeTriple(subject, 'lives_in', habitat, 'Habitat', sentence))
      })
    }

    if (/(保护等级|评级|列为)/.test(sentence)) {
      findAll(STATUSES, sentence).forEach((status) => {
        triples.push(makeTriple(subject, 'has_status', status, 'Status', sentence))
      })
    }

    if (/(威胁|面临)/.test(sentence)) {
      findAll(THREATS, sentence).forEach((threat) => {
        triples.push(makeTriple(subject, 'threatened_by', threat, 'Threat', sentence))
      })
    }
  }

  return uniqueTriples(triples)
}

export function extractTriplesFromDocuments(documents) {
  return uniqueTriples(
    documents.flatMap((document) => extractTriplesFromText(document.text))
  )
}
