import React from 'react';
import {
    Box,
    Heading,
    Text,
    useColorModeValue,
    Link
} from '@chakra-ui/react'
import { Link as RouterLink } from 'react-router-dom';
import { Card } from '../components/Card';
import { SignupForm } from '../components/AuthForm/SignupForm'

interface SignupPageProps {

}

const SignupPage: React.FC<SignupPageProps> = () => {
    return (
        <Box
        bg={useColorModeValue('gray.50', 'inherit')}
        minH="100vh"
        py="12"
        px={{ base: '4', lg: '8' }}
      >
        <Box maxW="md" mx="auto">
          <Box>Logo Placeholder</Box>
          <Heading textAlign="center" size="xl" fontWeight="extrabold">
            Sign up for an account
          </Heading>
          <Text mt="4" mb="8" align="center" maxW="md" fontWeight="medium">
            <Text as="span">Already have an account? </Text>
            <Link
                color={useColorModeValue('blue.500', 'blue.200')}
                _hover={{ color: useColorModeValue('blue.600', 'blue.300') }}
                display={{ base: 'block', sm: 'inline' }}
                as={RouterLink}
                to="/login">
                    Log in
            </Link>
          </Text>
          <Card>
            <SignupForm />
          </Card>
        </Box>
      </Box>

    );
}

export default SignupPage;