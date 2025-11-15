GET_REPOS_QUERY = """
query($cursor: String) {
  search(query: "stars:>1", type: REPOSITORY, first: 50, after: $cursor) {
    pageInfo {
      endCursor
      hasNextPage
    }
    edges {
      node {
        ... on Repository {
          id
          nameWithOwner
          stargazerCount
        }
      }
    }
  }
}
"""
