GET_REPOS_QUERY = """
query($query: String!, $first: Int!, $after: String) {
  search(query: $query, type: REPOSITORY, first: $first, after: $after) {
    repositoryCount
    pageInfo {
      endCursor
      hasNextPage
    }
    nodes {
      __typename
      ... on Repository {
        databaseId
        name
        owner {
          login
        }
        stargazerCount
        url
      }
    }
  }
  rateLimit {
    remaining
    resetAt
    cost
  }
}
"""
